document.addEventListener("DOMContentLoaded", function(){
    mySend('refresh','info',updateTable)
    mySend('serverip', 'ip-box', info)
    
});

let refresh_timeout;

function repeat_refresh() {

    mySend('refresh','info',updateTable)

// timeout is set to 4 seconds after last execution

    refresh_timeout = setTimeout(repeat_refresh, 4000);
}

function mySend(page, reply_node, render_it) {
//clearResponses()
a = "./" + page
var REST_CALL_DELAY_MS = 20;
var b = new XMLHttpRequest;
        b.onreadystatechange = function(){
            if (4 == b.readyState && 200 == b.status) {
                setTimeout(render_it(reply_node, b.responseText), REST_CALL_DELAY_MS);
               }
            if (4 == b.readyState && 404 == b.status) {
                document.getElementById('error-box').innerHTML = b.status;
                document.getElementById('response').innerHTML = b.responseText;
                }
            if (4 == b.readyState && 500 == b.status) {
                document.getElementById('error-box').innerHTML = b.status;
                document.getElementById('response').innerHTML = b.responseText;
                }
        };
        b.open("GET", a, !0);
        b.send();
}


function clearResponses() {
var nodes = document.querySelectorAll('.response')
if (nodes.length > 0) 
   { nodes.forEach(function(node) { node.innerHTML = "" }) }
}

function updateTable(tableId, text){
  json = JSON.parse(text)
  let tableHTML = "<tr>";
  jsonData = json['data'];
  
  Object.keys(jsonData)
        .sort()
        .forEach(function (header) {
        
    tableHTML += "<th>" + header + "</th>";
    devices = Object.keys(jsonData[header]).sort(function(a,b) {return Object.keys(jsonData[header][b]).length -  Object.keys(jsonData[header][a]).length}); 
 
    attributes = Object.keys(jsonData[header][devices[0]]).sort()
        for (var i in attributes) {
          tableHTML += "<th " 
          if (i == attributes.length-1) { tableHTML += "colspan='5'"}
          tableHTML += "> " + attributes[i] +"</th> "
          
         } 
    tableHTML += "</tr>";
    devices = Object.keys(jsonData[header]).sort();
    devices.forEach(function (device) {
            tableHTML += "<tr> <td> " + device + " </td>";
               for (var i in attributes) {
                 tableHTML += "<td "
                 if (i == attributes.length-1) { tableHTML += "colspan='5'"}
                 tableHTML += ">" + (jsonData[header][device][attributes[i]] || " ") + "</td>";
                   }
             })
    tableHTML += "</tr>";
  })

  document.getElementById(tableId).innerHTML = tableHTML;
}

function render(reply_node, text) {
object = JSON.parse(text)
clearResponses()
  document.getElementById(reply_node).innerHTML = JSON.stringify(object);
// mySend('refresh','info',updateTable)
}

//  need to think about the design of this bit, what is the response to a set display
//  Could it just be the JSON for a text - or perhaps check if the response is JSON
function info(node, text) {
   document.getElementById(node).innerHTML = text;
}

function display(reply_node, object) {
clearResponses()
  document.getElementById(reply_node).innerHTML = JSON.stringify(object);
  mysend('set-display?v1=20&v2=15', 'info', info('display set'))
}