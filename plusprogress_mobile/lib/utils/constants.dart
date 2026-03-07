class Constants {
 
  static const String baseUrl = 'http://192.168.0.117:8000';  /
  static const String apiUrl = '$baseUrl/api';
  
  // Эндпоинты
  static const String tokenEndpoint = '$apiUrl/token/';
  static const String refreshEndpoint = '$apiUrl/token/refresh/';
  static const String lessonsEndpoint = '$apiUrl/lessons/';
}