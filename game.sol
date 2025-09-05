contract Game {

    // verifies that boath boardCommitments are well-formed
    // player1 == msg.sender
    // generates a new gameId
    function newGame(uint boardCommitment1, bytes proof1, address player2, uint boardCommitment2, bytes proof2);

    
    // check if game is not finished
    // check if game exists and it's msg.sender's turn
    function move(uint gameId, uint position); // msg.sender is player

    // use stored boardCommitment and stored position to verify proof
    function revealHitOrMiss(uint gameId, bool isHit, bytes proof); // called by the other player

}