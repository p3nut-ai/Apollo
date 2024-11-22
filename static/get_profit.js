function fetchProfit() {
  $('#back_btn').click(function(e) {
  e.preventDefault(); // Prevent default button behavior

  $.ajax({
      url: '/clear_msg',
      method: 'GET',
      success: function(data) {
          $('#not_flag_container').show();
          $('#flag_container').hide();
          $('#edit_tp').val('');
      },
      error: function(xhr, status, error) {
          console.error("AJAX Error: ", status, error);
      }
  });

});
}
setInterval(fetchProfit, 2000); // Fetch profit every 5 seconds
