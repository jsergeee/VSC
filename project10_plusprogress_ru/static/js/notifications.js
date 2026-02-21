$(document).ready(function () {
  // Загружаем уведомления при загрузке страницы
  loadNotifications()

  // Обновляем каждые 30 секунд
  setInterval(loadNotifications, 30000)

  // Отметить все как прочитанные
  $('#markAllRead').click(function (e) {
    e.preventDefault()
    $.post('/api/notifications/mark-all-read/', function () {
      $('.notification-item').removeClass('unread')
      updateBadge(0)
    })
  })

  // Обработчик клика на уведомление
  $(document).on('click', '.notification-item', function (e) {
    var id = $(this).data('id')
    var link = $(this).data('link')

    // Отмечаем как прочитанное
    $.post('/api/notifications/' + id + '/read/', function () {
      // Если есть ссылка - переходим
      if (link) {
        window.location.href = link
      }
    })
  })
})

function loadNotifications () {
  $.get('/api/notifications/', function (data) {
    // Обновляем бейдж
    updateBadge(data.unread_count)

    // Обновляем список уведомлений
    var html = ''
    if (data.notifications.length === 0) {
      html = '<div class="text-center p-3 text-muted">Нет уведомлений</div>'
    } else {
      $.each(data.notifications, function (i, n) {
        var unreadClass = n.is_read ? '' : 'unread'
        var icon = getNotificationIcon(n.type)

        html += `
                    <div class="notification-item ${unreadClass}" data-id="${n.id}" data-link="${n.link}">
                        <div class="d-flex">
                            <div class="notification-icon">
                                ${icon}
                            </div>
                            <div class="notification-content">
                                <div class="notification-title">${n.title}</div>
                                <div class="notification-message">${n.message}</div>
                                <div class="notification-time">${n.created_ago}</div>
                            </div>
                        </div>
                    </div>
                `
      })
    }
    $('#notificationsList').html(html)
  })
}

function updateBadge (count) {
  var badge = $('#notificationBadge')
  if (count > 0) {
    badge.text(count).show()
  } else {
    badge.hide()
  }
}

function getNotificationIcon (type) {
  switch (type) {
    case 'lesson_reminder':
      return '<i class="fas fa-bell text-primary"></i>'
    case 'lesson_canceled':
      return '<i class="fas fa-times-circle text-danger"></i>'
    case 'lesson_completed':
      return '<i class="fas fa-check-circle text-success"></i>'
    case 'payment_received':
      return '<i class="fas fa-plus-circle text-success"></i>'
    case 'payment_withdrawn':
      return '<i class="fas fa-minus-circle text-warning"></i>'
    case 'material_added':
      return '<i class="fas fa-file text-info"></i>'
    default:
      return '<i class="fas fa-info-circle text-secondary"></i>'
  }
}
