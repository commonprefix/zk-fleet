// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.13;

import {Test, console} from "forge-std/Test.sol";
import {Game} from "../src/Game.sol";
import {Verifier as BoardVerifier} from "../src/BoardVerifier.sol"; 
import {Verifier as AttackVerifier} from "../src/AttackVerifier.sol"; 

contract GameTest is Test {
    Game public game;

    function setUp() public {
        BoardVerifier boardVerifier = new BoardVerifier();
        AttackVerifier attackVerifier = new AttackVerifier();
        game = new Game(boardVerifier, attackVerifier);
    }

    // TODO: add tests
}
