import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../models/models.dart';

const String _baseUrl = 'http://localhost:80/api/v1';

class ApiService {
  late final Dio _dio;
  final FlutterSecureStorage _storage = const FlutterSecureStorage();

  ApiService() {
    _dio = Dio(BaseOptions(
      baseUrl: _baseUrl,
      connectTimeout: const Duration(seconds: 10),
      receiveTimeout: const Duration(seconds: 30),
      headers: {'Content-Type': 'application/json'},
    ));

    _dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) async {
        final token = await _storage.read(key: 'access_token');
        if (token != null) options.headers['Authorization'] = 'Bearer $token';
        handler.next(options);
      },
      onError: (error, handler) async {
        if (error.response?.statusCode == 401) {
          final refreshed = await _refreshToken();
          if (refreshed) {
            final token = await _storage.read(key: 'access_token');
            error.requestOptions.headers['Authorization'] = 'Bearer $token';
            final response = await _dio.fetch(error.requestOptions);
            handler.resolve(response);
            return;
          }
        }
        handler.next(error);
      },
    ));
  }

  Future<AuthTokens> login(String email, String password, {String? totpCode}) async {
    final response = await _dio.post('/auth/login', data: {
      'email': email, 'password': password,
      if (totpCode != null) 'totp_code': totpCode,
    });
    final tokens = AuthTokens.fromJson(response.data);
    await _storage.write(key: 'access_token', value: tokens.accessToken);
    await _storage.write(key: 'refresh_token', value: tokens.refreshToken);
    return tokens;
  }

  Future<User> register({required String email, required String password, required String firstName, required String lastName, String? phone}) async {
    final response = await _dio.post('/auth/register', data: {
      'email': email, 'password': password,
      'first_name': firstName, 'last_name': lastName,
      if (phone != null) 'phone': phone,
    });
    return User.fromJson(response.data);
  }

  Future<User> getMe() async {
    final response = await _dio.get('/auth/me');
    return User.fromJson(response.data);
  }

  Future<void> logout() async {
    await _dio.post('/auth/logout');
    await _storage.deleteAll();
  }

  Future<Map<String, dynamic>> getAccounts() async {
    final response = await _dio.get('/accounts');
    return response.data;
  }

  Future<Account> createAccount(String type, String currency) async {
    final response = await _dio.post('/accounts', data: {'account_type': type, 'currency': currency});
    return Account.fromJson(response.data);
  }

  Future<Transaction> transfer({required String fromAccountId, required String toAccountId, required double amount, String currency = 'EUR', String? description, String? idempotencyKey}) async {
    final response = await _dio.post('/transactions/transfer', data: {
      'from_account_id': fromAccountId, 'to_account_id': toAccountId,
      'amount': amount, 'currency': currency,
      if (description != null) 'description': description,
      if (idempotencyKey != null) 'idempotency_key': idempotencyKey,
    });
    return Transaction.fromJson(response.data);
  }

  Future<Map<String, dynamic>> getTransactions(String accountId, {int page = 1, int perPage = 20}) async {
    final response = await _dio.get('/transactions', queryParameters: {'account_id': accountId, 'page': page, 'per_page': perPage});
    return response.data;
  }

  Future<Map<String, dynamic>> chat(String message, {List<Map<String, dynamic>> history = const [], Map<String, dynamic>? userContext}) async {
    final response = await _dio.post('/ai/chat', data: {
      'message': message, 'conversation_history': history,
      if (userContext != null) 'user_context': userContext,
    });
    return response.data;
  }

  Future<Map<String, dynamic>> getRecommendations(Map<String, dynamic> profile) async {
    final response = await _dio.post('/ai/recommendations', data: profile);
    return response.data;
  }

  Future<List<dynamic>> getNotifications({bool unreadOnly = false}) async {
    final response = await _dio.get('/notifications', queryParameters: {'unread_only': unreadOnly});
    return response.data;
  }

  Future<void> markAsRead(String notificationId) async {
    await _dio.patch('/notifications/$notificationId/read');
  }

  Future<bool> _refreshToken() async {
    try {
      final refreshToken = await _storage.read(key: 'refresh_token');
      if (refreshToken == null) return false;
      final response = await _dio.post('/auth/refresh', data: {'refresh_token': refreshToken});
      final tokens = AuthTokens.fromJson(response.data);
      await _storage.write(key: 'access_token', value: tokens.accessToken);
      await _storage.write(key: 'refresh_token', value: tokens.refreshToken);
      return true;
    } catch (_) { return false; }
  }
}

final apiService = ApiService();
