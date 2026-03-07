import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import '../utils/constants.dart';

class ApiService {
  static final ApiService _instance = ApiService._internal();
  factory ApiService() => _instance;
  ApiService._internal();

  Future<Map<String, String>> _getHeaders() async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('access_token');
    
    return {
      'Content-Type': 'application/json',
      'Authorization': token != null ? 'Bearer $token' : '',
    };
  }

  // Логин
  Future<Map<String, dynamic>> login(String username, String password) async {
    try {
      print('Отправка запроса на ${Constants.tokenEndpoint}');
      
      final response = await http.post(
        Uri.parse(Constants.tokenEndpoint),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'username': username, 'password': password}),
      ).timeout(Duration(seconds: 10));

      print('Статус ответа: ${response.statusCode}');
      print('Тело ответа: ${response.body}');

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        throw Exception('Ошибка входа: ${response.statusCode}');
      }
    } catch (e) {
      print('Ошибка соединения: $e');
      throw Exception('Ошибка соединения: $e');
    }
  }
}