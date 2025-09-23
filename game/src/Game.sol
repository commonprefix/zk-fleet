// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import {Verifier as BoardVerifier} from "./BoardVerifier.sol"; 
import {Verifier as AttackVerifier} from "./AttackVerifier.sol"; 

uint constant BOARD_DIMENSION = 11;
uint constant SHIP_COUNT = 3;
uint constant SHIP_LENGTH = 3;
uint constant TIMEOUT_PERIOD = 100; // in blocks, a constant for now
uint8 constant NO_TARGET = 255;

struct GameTracker {
    uint256 boardCommitment1; // the commitment to the board of player 1
    uint256 boardCommitment2; // the commitment to the board of player 2
    address player1;
    address player2;
    uint8 hitCounter1; // the number of ship parts hit by player 1
    uint8 hitCounter2; // the number of ship parts hit by player 2
    uint256 hitTargets1; // if bit b is set, this means that player1 already attacked position b
    uint256 hitTargets2; // if bit b is set, this means that player2 already attacked position b
    uint8 turn; // the turn number
    uint32 lastMove; // the block number of the last action of a player, used for timeout
    uint8 target; // stores the current target
    bool gameEnded; // if true, indicates that the game has ended
    bool winner; // if the game has ended, stores the winner
    uint stake; // player2 has to match the stake of player1 to join the game
    bool withdrawn; // indicates whether the winner has withdrawn the stake
}


contract Game {
    event NewGame(uint gameId, address player1, address player2, uint stake);
    event Attack(uint gameId, uint target);
    event GameWon(uint gameId, bool winner);

    mapping(uint => GameTracker) public games;
    uint public emptyGamePointer; // points toward the next empty game
    BoardVerifier boardVerifier;
    AttackVerifier attackVerifier;

    constructor(BoardVerifier _boardVerifier, AttackVerifier _attackVerifier) {
        boardVerifier = _boardVerifier;
        attackVerifier = _attackVerifier;
    }

    /**
     * Starts a new game
     * @param boardCommitment1 the commitment to the board this player will use in this game
     * @param proof1 the proof that the board behind the commitment is well-formed
     * @param player2 optional. If non-zero, only specified other address may join this game
     */
    function newGame(uint boardCommitment1, BoardVerifier.Proof calldata proof1, address player2) external payable {
        require(boardVerifier.verifyTx(proof1, [boardCommitment1]), "Proof that board is well-formed is invalid");
        GameTracker storage curGame = games[emptyGamePointer];
        curGame.player1 = msg.sender;
        curGame.boardCommitment1 = boardCommitment1;
        if (player2 != address(0)) {
            curGame.player2 = player2;
        }
        if (msg.value > 0) {
            curGame.stake = msg.value;
        }
        emit NewGame(emptyGamePointer, msg.sender, player2, msg.value);
        emptyGamePointer += 1;
    }

    function abortGame(uint gameId) external {
        GameTracker storage game = games[gameId];
        require(game.player1 == msg.sender, "Not your game");
        require(game.boardCommitment2 == 0, "Player2 already joined");
        require(game.gameEnded == false, "Game already aborted");

        // allow player1 to win the game and get their stake back
        _resolveWin(gameId, true); 
    }

    function timeoutGame(uint gameId) external {
        GameTracker storage game = games[gameId];
        require(game.gameEnded == false, "Game already ended");
        require(game.boardCommitment2 != 0, "Cannot timeout a game before it has begun");
        require(game.lastMove + TIMEOUT_PERIOD < block.number, "Game not yet timed out");
        // Don't have to check msg.sender, anyone can timeout a game 
        
        // check which player's turn it is
        bool winner;
        if(game.turn % 2 == 0) {
            if(game.target == NO_TARGET) {
                // on player1's turn, player1 did not attack
                winner = false; // player2 wins
            } else {
                // on player1's turn, player2 did not resolve the attack
                winner = true; // player1 wins
            }
        } else {
            if(game.target == NO_TARGET) {
                // on player2's turn, player1 did not attack
                winner = true; // player1 wins
            } else {
                // on player2's turn, player1 did not resolve the attack
                winner = false; // player2 wins
            }
        }
        _resolveWin(gameId, winner);
    }

    function joinGame(uint gameId, uint boardCommitment2, BoardVerifier.Proof calldata proof2) external payable {
        require(boardVerifier.verifyTx(proof2, [boardCommitment2]), "Proof that board is well-formed is invalid");
        GameTracker storage game = games[gameId];
        require(game.player1 != address(0), "Game does not exist");
        require(game.boardCommitment2 == 0, "Player2 already joined");
        require(game.gameEnded == false, "Game already aborted");
        
        if(game.player2 == address(0)) {
            // anyone can join
            game.player2 = msg.sender;
        } else {
            require(game.player2 == msg.sender, "This game is invite-only and you are not invited");
        }

        require(game.stake == msg.value, "Have to match the stake precisely");

        game.boardCommitment2 = boardCommitment2;
        game.lastMove = uint32(block.number); // start the game
    }

    function makeMove(uint gameId, uint8 target) external {
        GameTracker storage game = games[gameId];
        require(game.gameEnded == false, "Game has ended");
        require(game.target == NO_TARGET, "Previous turn not yet resolved");
        require(target < BOARD_DIMENSION * BOARD_DIMENSION, "Invalid target");

        if (game.turn % 2 == 0) {
            // this is player1's turn
            require(game.player1 == msg.sender, "Not your turn or game");
            require((2**target) & game.hitTargets1 == 0, "You already attacked this position");
            game.hitTargets1 += (2**target); // mark this target as hit
        } else {
            // this is player2's turn
            require(game.player2 == msg.sender, "Not your turn or game");
            require((2**target) & game.hitTargets2 == 0, "You already attacked this position");
            game.hitTargets2 += (2**target); // mark this target as hit
        }
        game.target = target;
        emit Attack(gameId, target);
        game.lastMove = uint32(block.number);
    }

    function resolveMove(uint gameId, uint isHit, AttackVerifier.Proof calldata proof) external {
        GameTracker storage game = games[gameId];
        require(game.gameEnded == false, "Game has ended");
        require(game.target != NO_TARGET, "Cannot resolve before a move has been made");
        // actually don't have to check for the player here - only someone that KNOWS the board can call this function
        uint boardUnderAttack;
        if(game.turn % 2 == 0) {
            // this is player1's attack on the board of player2
            boardUnderAttack = game.boardCommitment2;
            if(isHit == 1) {
                game.hitCounter1 += 1;
                if(game.hitCounter1 == SHIP_COUNT * SHIP_LENGTH) {
                    _resolveWin(gameId, true);
                }
            }
        } else {
            // this is player2's attack on the board of player1
            boardUnderAttack = game.boardCommitment1;
            if(isHit == 1) {
                game.hitCounter2 += 1;
                if(game.hitCounter2 == SHIP_COUNT * SHIP_LENGTH) {
                    _resolveWin(gameId, false);
                }
            }
        }
        require(attackVerifier.verifyTx(proof, [boardUnderAttack, isHit, game.target]), "Attack proof does not verify");
        game.target = NO_TARGET; // reset target
        game.turn += 1; // next turn
        game.lastMove = uint32(block.number);
    }

    function _resolveWin(uint gameId, bool winner) internal {
        GameTracker storage game = games[gameId];
        require(game.gameEnded == false, "Game has ended");
        game.gameEnded = true;
        game.winner = winner;
        emit GameWon(gameId, winner);
    }

    function withdraw(uint gameId) external {
        GameTracker storage game = games[gameId];
        require(game.gameEnded == true, "Game has not ended");
        require(game.withdrawn == false, "Stake already withdrawn");
        if(game.winner) {
            // you need to be player1
            require(game.player1 == msg.sender);
        } else {
            require(game.player2 == msg.sender);
        }
        
        uint amount = 0;
        if (game.boardCommitment2 == 0) {
            amount = game.stake; // player1 aborted the game; only refund the stake
        } else {
            amount = game.stake * 2; // get both player's stake
        }
        bool okay = payable(msg.sender).send(amount);
        require(okay, "Withdrawing failed");
    }
}