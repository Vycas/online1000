var xmlHttp = createXmlHttpRequestObject();

function getId() {
  var url = location.href;
  id = url.substr(url.lastIndexOf('/')+1);
  return id;
}

function sendMessage(url) {
  var xmlHttp = createXmlHttpRequestObject();
  
  if (xmlHttp) {
    try {
      xmlHttp.onreadystatechange = function() {
        if (xmlHttp.readyState == 4) {
          if (xmlHttp.status == 200) {
            return xmlHttp.responseText;
          }
          else {
            return false;
          }
        }
        else {
          return false;
        }
      }
      xmlHttp.open("GET", url, false);
      xmlHttp.send(null);
    }
    catch(e) {
      return false;
    }
    return true;
  }
  else {
    return false;
  }
}

function update() {
  var url = '/update/' + getId();
  
  if (xmlHttp) {
    try {
      xmlHttp.onreadystatechange = function() {
        if (xmlHttp.readyState == 4) {
          if (xmlHttp.status == 200) {
              var response = xmlHttp.responseText;
              eval('var dict = ' + response);
              document.getElementById('info_header').innerHTML = dict.info_header;
              document.getElementById('player_username').innerHTML = dict.player_username;
              document.getElementById('player_points').innerHTML = dict.player_points;
              document.getElementById('player_turn').innerHTML = dict.player_turn;
              document.getElementById('opponent1_username').innerHTML = dict.opponent1_username;
              document.getElementById('opponent1_points').innerHTML = dict.opponent1_points;
              document.getElementById('opponent1_turn').innerHTML = dict.opponent1_turn;
              document.getElementById('opponent2_username').innerHTML = dict.opponent2_username;
              document.getElementById('opponent2_points').innerHTML = dict.opponent2_points;
              document.getElementById('opponent2_turn').innerHTML = dict.opponent2_turn;
              controls = ['start', 'open', 'blind', 'bettings', 'bet', 'pass']
              myturn = dict.player_turn != '';
              for (var i=0; i<controls.length; i++) {
                document.getElementById(controls[i]).style.display = 'none';
              }
              switch (dict.state) {
                case 'waiting':
                  break;
                case 'ready':
                  if (myturn) {
                    document.getElementById('start').style.display = 'block';
                  }
                  break;
                case 'started':
                  document.getElementById('open').style.display = 'block';
                  document.getElementById('blind').style.display = 'block';
                  break;
                case 'go_blind':
                  document.getElementById('open').style.display = 'block';
                case 'go_open':
                  break;
              }
              
              var bettings = document.getElementById('bettings');
              if (dict.bettings) {
                bettings.style.display = 'block';
                for (var i=0; i<bettings.childNodes.length; i++) {
                  bettings.removeChild(bettings.childNodes[i]);
                }
                for (var i=0; i<dict.bettings.length; i++) {
                  option = document.createElement('option');
                  option.setAttribute('value', dict.bettings[i])
                  option.innerHTML = dict.bettings[i];
                  bettings.appendChild(option);
                }
              }
              
              for (var i=1; i<=3; i++) {
                eval("var e=document.getElementById('bank"+i+"'); var v=dict.bank["+(i-1)+"]; "+
                     "e.src='/images/cards/'+v+'.gif'; e.style.display=v?'inline':'none';");
              }
              for (var i=1; i<=10; i++) {
                eval("var e=document.getElementById('card"+i+"'); var v=dict.cards["+(i-1)+"]; "+
                     "e.src='/images/cards/'+v+'.gif'; e.style.display=v?'inline':'none';");
              }
          }
          else {
            alert(xmlHttp.statusText);
          }
        }
      }
      xmlHttp.open("GET", url, true);
      xmlHttp.send(null);
    }
    catch(e) {
      alert(e.toString());
    }
  }
}

function post(cmd) {
  var url = '/' + cmd + '/' + getId();
  sendMessage(url);
  update();
}

function leave() {
  location.href = '/sessions'
}