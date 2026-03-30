// Получаем элементы
const burger = document.getElementById('burger');
const nav = document.querySelector('.nav');
const overlay = document.querySelector('.overlay');

// Создаем оверлей, если его нет в HTML
if (!overlay) {
  const newOverlay = document.createElement('div');
  newOverlay.className = 'overlay';
  document.body.appendChild(newOverlay);
}

const overlayElement = document.querySelector('.overlay');

// Функция открытия/закрытия меню
function toggleMenu() {
  burger.classList.toggle('active');
  nav.classList.toggle('active');
  overlayElement.classList.toggle('active');
  
  // Блокируем прокрутку страницы при открытом меню
  if (nav.classList.contains('active')) {
    document.body.style.overflow = 'hidden';
  } else {
    document.body.style.overflow = '';
  }
}

// Слушаем клик по бургеру
burger.addEventListener('click', toggleMenu);

// Закрываем меню при клике на оверлей
overlayElement.addEventListener('click', toggleMenu);

// Закрываем меню при клике на ссылку (опционально)
const navLinks = document.querySelectorAll('.nav__link');
navLinks.forEach(link => {
  link.addEventListener('click', () => {
    if (nav.classList.contains('active')) {
      toggleMenu();
    }
  });
});

// Закрываем меню при изменении размера экрана (если стали десктопом)
window.addEventListener('resize', () => {
  if (window.innerWidth > 768) {
    if (nav.classList.contains('active')) {
      burger.classList.remove('active');
      nav.classList.remove('active');
      overlayElement.classList.remove('active');
      document.body.style.overflow = '';
    }
  }
});