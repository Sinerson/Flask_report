    let timeleft = 10;
    let Timer = setInterval(function(){
  if(timeleft <= 0){
    clearInterval(downloadTimer);
  }
  document.getElementById("progressBar").value = 11 - timeleft;
  timeleft -= 1;
}, 1000);