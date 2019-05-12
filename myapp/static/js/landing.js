var landing = landing || {};

landing.fetch = function(url, method, data, params){
  return fetch(url, {
    method: method,
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(data)
  }).then(function(response) {
    if (response.status == 200) {
      return response.json();
    }
    throw new Error('Unexpected status code: ' +  response.status);
  });
};

landing.handleError = function(err){
    console.log(err);
};

landing.fetchPolling = function(task_id){
    var url = window.origin + '/polling/' + task_id;
    fetch(url)
        .then(function(response) {
            return response.json();
        })
        .then(function(myJson) {
            if (myJson === 'SUCCESS') {
                window.location = window.origin + '/detail/' + task_id;
            } else if (myJson === 'pending') {
                console.log('result pending');
                if ($('#working-onit').length === 0) {
                    landing.addSpinningWheel();
                }
                setTimeout(landing.fetchPolling, 5000, task_id);
            } else if (myJson === 'ERROR') {
                $('#working-onit').remove();
                landing.showErrorPanel();
                throw new Error("Task status is error");
            }
        })
        .catch(function(error) {
            console.log("Error: " + error);
        });
},

landing.loadFile = function(files){
  if (files.length == 0) {
    $('#line-names').empty();
    $('#task-name').val('');
  }
  if (files.length > 1) {
    alert('Please choose only one file.');
    return;
  }
  var reader = new FileReader();
  reader.onload = function(e) {
      $('#line-names').text(e.target.result);
      $('#task-name').val((files[0].name).split('.txt')[0]);
  };
  reader.readAsText(files[0]);
},

landing.checkUserName = function(userName){
    const userRequest = new Request(userConfigUrl + '/' + userName, {
            method: 'GET',
            headers: {
                'content-type': 'application/json'
            },
        });

        fetch(userRequest)
        .then(function(response) {
            if (response.status == 200) {
                return response.json();
            }
            $('#generate-crosses').attr("disabled", "disabled");
            throw new Error("Unexpected response status: " + response.status);
        })
        .then(function(data) {
            if (data['config'] && data['config']['id']) {
                // valid user found
                $('#generate-crosses').removeAttr('disabled');
            }
        })
        .catch(function(error) {
            console.log("Error: " + error);
        });
},

$(document).ready(function(){
    $('#file-upload').on('change', function(event) {
      landing.loadFile(event.target.files);
    });

    var initialName = $('#user-name')[0].value;
    if (initialName) {
        landing.checkUserName(initialName.toLowerCase());
    }
    else {
        $('#generate-crosses').attr("disabled", "disabled");
    }

    // collect all information to be send as POST request to backend
    $('#generate-crosses').on('click', function(event){
        let data = {
            'lnames': $('#line-names')[0].value,
            'aline': $('#a-line')[0].value,
            'task_name': $('#task-name')[0].value,
            'show-all': $('#show-all')[0].checked
        };
        var userInput = $('#user-name')[0];
        var user = null;
        if (userInput) {
            user = userInput.value.toLowerCase();
        }
        const jsonData = JSON.stringify(data);
        const url = window.origin + '/compute_splits/' + user;

        const calculateRequest = new Request(url, {
            method: 'POST',
            body: jsonData,
            headers: {
                'content-type': 'application/json'
            },
        });

        fetch(calculateRequest)
        .then(function(response) {
            if (response.status == 200) {
                return response.json();
            }
            throw new Error("Unexpected response status: " + response.status);
        })
        .then(function(data) {
            if (!data.task_id) {
                throw new Error("Unexpected response format: no task ID found");
            }
            if (data.status !== 'QUEUED') {
                throw new Error("Task couldn't be queued. Its status is: " + data.status);
            }

            if (data){
                landing.fetchPolling(data.task_id);
            }
        })
        .catch(function(error) {
            console.log("Error: " + error);
        });
    });

    $('#user-name').on('keyup', function(event){
        var checkName = this.value.toLowerCase();
        landing.checkUserName(checkName);
    })
});