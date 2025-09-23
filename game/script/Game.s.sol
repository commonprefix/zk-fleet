// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.13;

import {Script, console} from "forge-std/Script.sol";
import {Game} from "../src/Game.sol";
import {Verifier as BoardVerifier} from "../src/BoardVerifier.sol"; 
import {Verifier as AttackVerifier} from "../src/AttackVerifier.sol"; 

contract GameScript is Script {
    Game public game;

    function setUp() public {}

    function run() public {
        vm.startBroadcast();

        BoardVerifier boardVerifier = new BoardVerifier();
        AttackVerifier attackVerifier = new AttackVerifier();

        game = new Game(boardVerifier, attackVerifier);

        vm.stopBroadcast();
    }
}
