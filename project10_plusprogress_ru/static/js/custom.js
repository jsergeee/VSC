$(window).on('load', function () {
  'use strict'

  /* ========================================================== */
  /*   Navigation Background Color                              */
  /* ========================================================== */

  $(window).on('scroll', function () {
    if ($(this).scrollTop() > 230) {
      $('.navbar-fixed-top').addClass('opaque')
    } else {
      $('.navbar-fixed-top').removeClass('opaque')
    }
    if ($(this).scrollTop() > 500) {
      $('#blink').removeClass('d-none')
    } else {
      $('#blink').addClass('d-none')
    }
  })

  /* ========================================================== */
  /*   Hide Responsive Navigation On-Click                      */
  /* ========================================================== */

  $('.navbar-nav li a').on('click', function (event) {
    $('.navbar-collapse').collapse('hide')
  })

  /* ========================================================== */
  /*   Navigation Color                                         */
  /* ========================================================== */

  $('#navbarCollapse').onePageNav({
    filter: ':not(.external)'
  })

  /* ========================================================== */
  /*   SmoothScroll                                             */
  /* ========================================================== */

  $('.navbar-nav li a, a.scrool').on('click', function (e) {
    var full_url = this.href
    var hash = this.hash // Получаем только часть после #

    // Проверяем, что это якорная ссылка (содержит #)
    if (hash && hash.length > 1) {
      e.preventDefault()
      var target = $(hash)

      if (target && target.length) {
        var target_top = target.offset().top
        $('html,body').animate({ scrollTop: target_top - 70 }, 1000)
      }
    }
    // Если нет hash - ничего не делаем, ссылка работает как обычно
  })

  /* ========================================================== */
  /*   Register Top Home Section                                */
  /* ========================================================== */

  $('#register-form-home').submit(function (e) {
    e.preventDefault()
    var fData = $(this).serialize()
    console.log(fData)
    $.ajax({
      url: '/php/register.php',
      method: 'post',
      dataType: 'html',
      data: fData,
      success: function () {
        if (1) {
          $('#register-form-home').fadeOut('fast', function () {
            $(this).siblings('p.register_success_box_home').show()
          })
        } else alert('Ошибка заполнения формы!')
      }
    })
  })
  $('#register-form-home-2').submit(function (e) {
    e.preventDefault()
    var fData = $(this).serialize()
    console.log(fData)
    $.ajax({
      url: '/php/register.php',
      method: 'post',
      dataType: 'html',
      data: fData,
      success: function () {
        if (1) {
          $('#register-form-home-2').fadeOut('fast', function () {
            $(this).siblings('p.register_success_box_home').show()
          })
        } else alert('Ошибка заполнения формы!')
      }
    })
  })

  /* ========================================================== */
  /*   Register                                                 */
  /* ========================================================== */

  $('#register-form').each(function () {
    var form = $(this)
    //form.validate();
    form.submit(function (e) {
      if (!e.isDefaultPrevented()) {
        jQuery.post(
          this.action,
          {
            names: $('input[name="register_names"]').val(),
            email: $('input[name="register_email"]').val()
          },
          function (data) {
            form.fadeOut('fast', function () {
              $(this).siblings('p.register_success_box').show()
            })
          }
        )
        e.preventDefault()
      }
    })
  })

  /* ========================================================== */
  /*   Contact                                                 */
  /* ========================================================== */

  $('#contact-form').each(function () {
    var form = $(this)
    //form.validate();
    form.submit(function (e) {
      if (!e.isDefaultPrevented()) {
        jQuery.post(
          this.action,
          {
            names: $('input[name="contact_names"]').val(),
            phone: $('input[name="contact_phone"]').val(),
            email: $('input[name="contact_email"]').val(),
            ticket: $('select[name="contact_ticket"]').val(),
            message: $('textarea[name="contact_message"]').val()
          },
          function (data) {
            form.fadeOut('fast', function () {
              $(this).siblings('p.contact_success_box').show()
            })
          }
        )
        e.preventDefault()
      }
    })
  })
})

/* ========================================================== */
/*   Popup-Gallery                                            */
/* ========================================================== */
$('.popup-gallery')
  .find('a.popup1')
  .magnificPopup({
    type: 'image',
    gallery: {
      enabled: true
    }
  })

$('.popup-gallery')
  .find('a.popup2')
  .magnificPopup({
    type: 'image',
    gallery: {
      enabled: true
    }
  })

$('.popup-gallery')
  .find('a.popup3')
  .magnificPopup({
    type: 'image',
    gallery: {
      enabled: true
    }
  })

$('.popup-gallery')
  .find('a.popup4')
  .magnificPopup({
    type: 'iframe',
    gallery: {
      enabled: false
    }
  })
