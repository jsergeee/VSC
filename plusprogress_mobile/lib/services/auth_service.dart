import 'package:shared_preferences/shared_preferences.dart';
import 'api_service.dart';
import '../models/user.dart';

class AuthService {
  static final AuthService _instance = AuthService._internal();
  factory AuthService() => _instance;
  AuthService._internal();

  User? _currentUser;
  User? get currentUser => _currentUser;

  Future<bool> login(String username, String password) async {
    try {
      final response = await ApiService().login(username, password);
      
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString('access_token', response['access']);
      await prefs.setString('refresh_token', response['refresh']);
      
      print('Токены сохранены!');
      
      // TODO: Получить данные пользователя через отдельный запрос
      _currentUser = User(
        id: 1,
        username: username,
        email: '$username@example.com',
        role: 'student',
      );
      
      return true;
    } catch (e) {
      print('Login error: $e');
      return false;
    }
  }

  Future<void> logout() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('access_token');
    await prefs.remove('refresh_token');
    _currentUser = null;
  }

  Future<bool> isLoggedIn() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.containsKey('access_token');
  }
}
