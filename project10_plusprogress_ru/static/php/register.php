<?php

$field__name = trim($_POST['name']);

$field__email = trim($_POST['email']);

$field__phone = trim($_POST['phone']);

$field__subject = trim($_POST['subject']);



if (strlen($field__name) > 15  OR strlen($field__email) > 30 OR strlen($field__phone) > 30){
    die();
}


$mail_to = 'jserge@yandex.ru';

$subject = 'Новая заявка на бесплатный пробный урок от: '.$field__name;

$headers = "Content-type: text/html; charset=utf-8 \r\n";

$body_message = 'Имя: '.$field__name."\n"."\n".'Почта: '.$field__email."\n"."\n".'Телефон: '.$field__phone."\n"."\n".'Предмет: '.$field__subject."\n";

$mail_status = mail($mail_to, $subject, $body_message, $headers);

echo 1;
die();
