let on_time


console.log('ws://' + window.location.host +
            '/ws/main/')
var socket = new WebSocket(
            'ws://' + window.location.host +
            '/ws/main/');

socket.onmessage = function (e) {
            var message = JSON.parse(e.data);
            console.log(message["type"])

            if(message["type"] === "friend_request"){
                let sent_from = message['sent_from']
                let friend_request_id = message['friend_request_id']
                document.getElementById("notif").innerHTML = `
                Your have received an invitation from ${sent_from}
                <button>decline</button>
                <button id ="acceptFriendReq">accept</button>`
                
                document.getElementById("acceptFriendReq").onclick = function(){
                    acceptFriendRequest(sent_from , friend_request_id)
                }
            }

            else if(message["type"] === "party_invite_receive"){

                        // Appears the notification
                        let party_invite_from = message['from']
                        $('#partyInviteModal').modal({backdrop: 'static', keyboard: false})  
                        $("#partyInviteModal").modal('show')

                        on_time = setTimeout( rejectPartyInvite , 30000)


                        // Timer
                        let seconds = 28
                        var timer_web = setInterval(function () {
                            $("#time").text(seconds);
                            seconds--
                        }, 1000);

                        document.getElementById("acceptPartyInvite").onclick = function() {

                            clearTimeout(on_time)
                            clearInterval(timer_web)
                            document.getElementById("pi_notif").innerHTML= ''

                            // Connects user to the party socket
                            let party_code= message['party_code']
                            partySocketConnection(party_code)

                        }
                        document.getElementById("rejectPartyInvite").onclick = function() {
                            clearTimeout(on_time)
                            clearInterval(timer_web)
                            rejectPartyInvite()

                        }
                    }


            else if(message["type"] ==="party_created"){

                let party_code = message['party_code']
                partySocketConnection(party_code)

            }

            else if (message["type"] === "match_making_started"){
                let started_at = message["started_at"]
                let is_searching = message["is_searching"]
                $("#searching").html(`
                    <p>Searching...</p>
                    <p>started at ${started_at}</p>
                    <button type="button" class="btn btn-info" onclick="cancelMatch()">Cancel</button>
                `)
            }

            else if (message["type"] === "match_found"){
                console.log("sfsdf")
                $("#searching").html(`
                    <p>Match Found</p>
                    <button type="button" class="btn btn-info" onclick="joinMatch(${nessage["match_id"]})">Accept</button>
                `)

            }
            
            
    };
console.log(party_socket)



function sendFriendRequest(userSelected){
    socket.send(JSON.stringify({'type': 'friend_request', 'sent_from': username
        , 'sent_to': userSelected}));
}

function acceptFriendRequest(sent_from , friend_request_id){
    document.getElementById("notif").innerHTML =''
    socket.send(JSON.stringify({'type': 'friend_request_accept', 'sent_from': sent_from,
    'sent_to': username, 'friend_request_id': friend_request_id}));
}

function rejectFriendRequest(friend_request_id){
    document.getElementById("notif").innerHTML =''
    socket.send(JSON.stringify({'type': 'friend_request_reject','friend_request_id': friend_request_id}));
}

socket.onclose = function(e) {
        console.error('Socket closed unexpectedly');
};

//--------------------------------------------------------------------------


function createParty(){
    socket.send(JSON.stringify({"type":"create_party"}))
}

function sendPartyInvite(userSelected){
    party_socket.send(JSON.stringify({"type": "party_invite_send",
    "sent_to": userSelected }))
}
function leaveParty(){
    party_socket.send(JSON.stringify({"type":"leave_party" }))
    console.log("left party")
}

function kickMember(member){
    party_socket.send(JSON.stringify({"type":"party_kick", "kicked_user":member}))
}

function promoteMember(member){
    party_socket.send(JSON.stringify({"type":"promote", "new_party_leader":member}))
}

function changePartyBar(party_members , party_quantity){
    let party_members_render = ""
    let user_is_party_leader = false

    //Checks wether the user is the partyleader or not
    for (let i = 0; i < party_quantity; i++){
        if(party_members[i]["is_party_leader"] && party_members[i]["username"] == username){
            user_is_party_leader = true
        }
    }

    if(user_is_party_leader){
        for (let i = 0; i < party_quantity; i++) {
            if(party_members[i]["username"] != username){
            party_members_render += `
                <div class="dropdown partyWrapper">
                    <button  class="member " id="${party_members[i]["username"]}" type="button" id="dropdownMenuButton" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
                    <img class="avatar-sm" src="${party_members[i]["profile_pic_url"]}">
                    </button>

                    <div class="dropdown-menu" aria-labelledby="dropdownMenuButton">
                        <center>
                            <img class="avatar-lg" src="${party_members[i]["profile_pic_url"]}">
                            <p>${party_members[i]["username"]}</p>
                        </center>
                        
                        <a class="dropdown-item" href="#">View Profile</a>
                        <div class="dropdown-divider"></div>
                        <button onclick="kickMember('${party_members[i]["username"]}')" class="dropdown-item" >Kick</button>
                        <button onclick="promoteMember('${party_members[i]["username"]}')" class="dropdown-item" >Prmote</button>
                    </div>
                </div>
                `  
            }else{
                    party_members_render += `
                    <button type="button" class="position-relative member">
                        <img class="avatar-sm" src="${party_members[i]["profile_pic_url"]}">
                        <span class="position-absolute top-0 start-100 translate-middle p-2 bg-warning border border-light rounded-circle">
                            
                            <span class="visually-hidden">New alerts</span>
                        </span>
                    </button>

                    `
                }
        }
    }else{
        for (let i = 0; i < party_quantity; i++){
        if(party_members[i]["username"] != username){
            if(party_members[i]['is_party_leader']){
                party_members_render += `
                    <div class="dropdown partyWrapper">
                        <button  class="member " id="${party_members[i]["username"]}" type="button" id="dropdownMenuButton" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
                        <img class="avatar-sm" src="${party_members[i]["profile_pic_url"]}">
                        <span class="position-absolute top-0 start-100 translate-middle p-2 bg-warning border border-light rounded-circle"> 
                            <span class="visually-hidden">New alerts</span>
                        </span>
                        </button>
                        

                        <div class="dropdown-menu" aria-labelledby="dropdownMenuButton">
                            <center>
                                <img class="avatar-lg" src="${party_members[i]["profile_pic_url"]}">
                                <p>${party_members[i]["username"]}</p>
                            </center>
                            
                            <a class="dropdown-item" href="#">View Profile</a>
                        </div>
                    </div>
                    `
            }else{
                party_members_render += `
                    <div class="dropdown partyWrapper">
                        <button  class="member " id="${party_members[i]["username"]}" type="button" id="dropdownMenuButton" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
                        <img class="avatar-sm" src="${party_members[i]["profile_pic_url"]}">
                        </button>

                        <div class="dropdown-menu" aria-labelledby="dropdownMenuButton">
                            <center>
                                <img class="avatar-lg" src="${party_members[i]["profile_pic_url"]}">
                                <p>${party_members[i]["username"]}</p>
                            </center>
                            
                            <a class="dropdown-item" href="#">View Profile</a>
                        </div>
                    </div>
                    `
            }
        }
        else{
            party_members_render += `
            <button  class="member">
            <img class="avatar-sm" src="${party_members[i]["profile_pic_url"]}">
            </button>
            `
        }
        }
    }

    for (let i = 0; i < 5 - party_quantity; i++) {
        party_members_render += `<button onclick="location.href='http://127.0.0.1:8000/accounts/friends/';" class="member" id="m${party_quantity + 1 + i}">+</button>\n` 
    }

    party_members_render += "<button id='leave' class='member'> ✖ </button>";

    document.getElementById("partyMembers").innerHTML = party_members_render

    document.getElementById("leave").onclick = leaveParty

}

function editPartyMessage(user_input,message_id){
    let encoded_user_input = user_input.replace(/&/g, "&amp;").replace(/>/g, "&gt;").replace(/</g, "&lt;").replace(/"/g, "&quot;").replace(/'/g, "&apos;")

    party_socket.send(JSON.stringify({"type":"party_send_message", "text":encoded_user_input , "message_id":message_id , "edited":true}))
}

function sendPartyMessage(user_input){
    let encoded_user_input = user_input.replace(/&/g, "&amp;").replace(/>/g, "&gt;").replace(/</g, "&lt;").replace(/"/g, "&quot;").replace(/'/g, "&apos;")

    party_socket.send(JSON.stringify({"type":"party_send_message", "text":encoded_user_input , "edited":false}))
}

function partySocketConnection(party_code){
    party_socket = new WebSocket(
        'ws://' + window.location.host +
        '/ws/party_chat/' + party_code + '/');

    console.log("Youve already had a party")

    party_socket.onmessage = function (e) {
        var party_message = JSON.parse(e.data);

        console.log(party_message["type"])

            switch (party_message["type"]) {

                case "party_members":
                    let party_members = party_message['info']
                    let party_quantity = party_members.length
                    changePartyBar(party_members , party_quantity)
                    if( party_quantity == 5){
                        Array.from(document.getElementsByClassName("spi")).forEach(function(element) {
                            element.disabled = true
                        })
                    }
                
                case "party_message":
                    console.log("miad inja")
                    let text = party_message['text']
                    let time = party_message['time']
                    let sent_from = party_message['sent_from']
                    let is_edited = party_message['edited']
                    console.log(is_edited)
                    let id = party_message['id']
                    console.log(sent_from)

                    if(is_edited){
                            $("#"+ id + "_text").html(text)
                            $("#" + id + "_time").html(`
                            ${time.slice(11 , 16)}
                            (edited)
                            `)
                    }else{
                        if(sent_from == username){
                        $("#conversation").append(`
                        <div id="${id}_body" class="message-body">
                            
                            <div class="col-sm-12 message-main-sender">
                                <div class="sender">
                                <div id="${id}_text" class="message-text">
                                    ${text}
                                </div>
                                <button id="${id}" type="button" class="btn btn-primary btn-sm editButton">Edit</button>
                                <div id="${id}_editBar"></div>
                                <span id="${id}_time" class="message-time pull-right">
                                ${time.slice(11 , 16)}
                                </span>
                                </div>
                            </div>
                            </div>
                        </div>
                        `)
                        }else{
                        $("#conversation").append(`
                        <div id="${id}_body" class="message-body">
                            <div>
                                <img class="avatar-sm" src="">
                                ${sent_from}
   con                         </div>
                            <div class="col-sm-12 message-main-receiver">
                                <div class="receiver">
                                <div id="${id}_text" class="message-text">
                                    ${text}
                                </div>
                                <span id="${id}_time" class="message-time pull-right">
                                    ${time.slice(11 , 16)}
                                </span>
                                </div>
                            </div>
                            </div>`)
                        }
                    }

                    let index = document.getElementsByClassName("editButton").length - 1
                    document.getElementsByClassName("editButton")[index].onclick = function(){

                        var id = document.getElementsByClassName("editButton")[index].id
                        var id_editBar =  id + "_editBar"

                        document.getElementById(id_editBar).innerHTML = `
                          <form>
                            <input type="text" id="${id}_editInput">
                            <button type="button" id="${id}_editbutton">send</button>
                            <button type="button" id="${id}_editCancel>cancel</button>
                          </form>
                        `
                        
                        let id_editInput =  id + "_editInput"
                        let id_editButton =  id + "_editbutton"
                        let id_editCancel =  id + "_editCancel"

                        document.getElementById(id_editButton).onclick = function(){

                          if(document.getElementById(id_editInput).value){
                            editPartyMessage(document.getElementById(id_editInput).value , id)
                            document.getElementById(id_editBar).innerHTML = ""

                          }else{
                            document.getElementById(id_editBar).innerHTML = ""
                          }
                        }
                    }

                }
                
    };


    party_socket.onclose = function(e) {
        document.getElementById("partyMembers").innerHTML ="<button type='button'class='btn btn-primary' id='createOrLeaveParty' onclick='createParty()'>create party</button>"
    }
}


// --------------------------------------------------

function findMatch(game_name){
    console.log("gets here")
    socket.send(JSON.stringify({"type":"find_a_match", "game_name":game_name}))
}


function cancelMatch(){
    socket.send(JSON.stringify({"type":"cancel_matchmaking"}))
}

function joinMatch(matchId){
    socket.send(JSON.stringify({"type":"join_the_match" , 'match_id':matchId}))
}