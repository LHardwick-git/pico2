{% args devices, dev_type, dev_names %}
<html>
<head>
    <link rel="stylesheet" type="text/css" href="styles.css">
    <link rel="stylesheet" type="text/css" href="check_styles.css">
    <title>PICO monitoring</title>

</head>
<body>
<div id='page'>
<div class=lh>
<!-- Calls to mysend are text to send / node for answer / render method-->
<h1>Page to modify device names</h1>

<form action = "" method='post'>
<table id='info'>
<tr><th>Device</th><th>Name</th><th>Connected</th><th>Type</th><th>Hide</th><th>Min/Max</th></tr>

<!-- Substituting on 'devices' calls the main devices table, then the types table, then the dev_name/minmax table-->

{% for key in devices %}
    <tr>
    <td>{{key}}</td>
     
    
    <td><input name ='{{key}}_Name' value = '{{ devices[key][' Name']}}' type = 'text' size = '16' /></td>
    <td>{{ devices[key]['Connected'] }}</td>
    <td>{{ dev_type[key] }}</td>
    
    
    <td class = "cb-td"><label class="container"><input name ='{{key}}_hide' type = 'checkbox'	{{dev_names.get(key+"_hide", "")}} />
        <span class="checkmark"></span></label></td>
        
    <td class = "cb-td"><label class="container"><input name ='{{key}}_minmax'       type = 'checkbox'	{{dev_names.get(key+"_minmax", "")}} />
        <span class="checkmark"></span></label></td>

    </tr>
{% endfor %} 



</table>
</br>
<table>
    <tr>
    <td><input class = 'button' type="submit" value="Update Configuration"></td>
    <td><button onclick="document.location='/'" type ='button'>Main Page</button></td>
    </tr>
</table>
</form>

</div>

</div>
</body>
</html>