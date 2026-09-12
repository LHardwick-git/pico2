{% args host %}
<html>
<head>
    <title>PICO monitoring</title>
    <link rel="stylesheet" type="text/css" href="styles.css"> 
    <script src="script.js"></script>
</head>
<div id='page'>
<div class=lh>

<h1>Device List {{host}}</h1>

<table id='info'>
</table>

</br>
</br>

<!-- Calls to mysend are text to send / node for answer / render method-->

<table id='info2'>
<tr>
    <td class="button-row"><button onclick="mySend('ping-temp', 'response', render)">Read Temps</button></td>
    <td class="button-row"><button onclick="mySend('ping-state', 'response', render)">Read States</button></td>
    <td class="button-row"><button onclick="mySend('ping-volts', 'response', render)">Read Voltages</button></td>

</tr>
<tr>
    <td><button onclick="document.location='/devconfig.tpl'" type ='button'>Edit configuration</button></a></td>
    <td colspan="2"><button onclick="mySend('delete-all', 'response', render)">Forget all</button> Clear device list (rescan)</td>

</tr>

<tr>
    <td><button onclick="mySend('clear-relay', 'response', render)">Clear relays</button></td>
    <td><button onclick="mySend('set-relay', 'response', render)">Set relays</button></td>
    <td><button onclick="mySend('serverip', 'ip-box', info)">Server IP</button></td>
</tr>

<tr>
    <td><button onclick="mySend('refresh', 'info', updateTable)">Refresh table</button></td>
    <td><button onclick="repeat_refresh()">Continual</button></td>
    <td><button onclick="clearTimeout(refresh_timeout)">Cancel</button></td>

</tr>
<tr>
<td><button onclick="mySend('div-zero', 'response', render)">Cause div-zero</button></td><td></td>
<td><button onclick="mySend('exit', 'response', info)">Exit</button></td>

</tr>
</table>

</div>

</br>
<span id='response' class="response" >Responses here</span>

</br>
<span id='error-box' class="response" >no error</span>

</br>Server IP address
<span id='ip-box' class="response" >IP-addr</span>

</div>
<div><img src='bath2.jpeg' width="800" /></div>

</html>	
