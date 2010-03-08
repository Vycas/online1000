var xmlHttp = createXmlHttpRequestObject();

function update(id) {
  var xmlHttp = createXmlHttpRequestObject();
  var url = '/update/' + id
  
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