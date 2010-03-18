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
              var controls = ['start', 'open', 'blind', 'bettings', 'bet', 'pass']
              var myturn = dict.player_turn != '';
              for (var i=0; i<controls.length; i++) {
                hide(controls[i]);
              }
              switch (dict.state) {
                case 'waiting':
                  break;
                case 'ready':
                  if (myturn) {
                    show('start');
                  }
                  break;
                case 'open_or_blind':
                  show('open');
                  show('blind');
                  break;
                case 'go_blind':
                  show('open');
                case 'go_open':
                if (myturn && !dict.passed) {
                    show('bettings');
                    show('bet');
                    if (!dict.first) {
                      show('pass');
                    }
                    add_bets(dict.bettings)
                  }
                  break;
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

function show(element) {
  document.getElementById(element).style.display = 'block';
}

function hide(element) {
  document.getElementById(element).style.display = 'none';
}

function add_bets(bets) {
  if (bets) {
    var bettings = document.getElementById('bettings');
    while (bettings.childNodes.length > 0) {
      bettings.removeChild(bettings.childNodes[0]);
    }
    for (var i=0; i<bets.length; i++) {
      option = document.createElement('option');
      option.setAttribute('value', bets[i])
      option.innerHTML = bets[i];
      bettings.appendChild(option);
    }
  }
}

function bet() {
  var bettings = document.getElementById('bettings');
  var bet = bettings.options[bettings.selectedIndex].value;
  var url = '/bet/' + getId() + '/' + bet;
  sendMessage(url);
  update();
}

function post(cmd, id) {
  var url = '/' + cmd + '/' + getId();
  sendMessage(url);
  update();
}

function leave() {
  location.href = '/sessions'
}