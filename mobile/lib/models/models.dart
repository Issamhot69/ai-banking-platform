class User {
  final String id;
  final String email;
  final String? phone;
  final String firstName;
  final String lastName;
  final bool isActive;
  final bool isVerified;
  final String kycStatus;
  final bool is2faEnabled;
  final DateTime createdAt;

  const User({required this.id, required this.email, this.phone, required this.firstName, required this.lastName, required this.isActive, required this.isVerified, required this.kycStatus, required this.is2faEnabled, required this.createdAt});

  String get fullName => '$firstName $lastName';

  factory User.fromJson(Map<String, dynamic> json) => User(
    id: json['id'], email: json['email'], phone: json['phone'],
    firstName: json['first_name'], lastName: json['last_name'],
    isActive: json['is_active'], isVerified: json['is_verified'],
    kycStatus: json['kyc_status'], is2faEnabled: json['is_2fa_enabled'],
    createdAt: DateTime.parse(json['created_at']),
  );
}

class Account {
  final String id;
  final String userId;
  final String accountNumber;
  final String? iban;
  final String accountType;
  final String currency;
  final double balance;
  final double availableBalance;
  final String status;
  final bool isPrimary;
  final double dailyTransferLimit;
  final double monthlyTransferLimit;
  final DateTime createdAt;

  const Account({required this.id, required this.userId, required this.accountNumber, this.iban, required this.accountType, required this.currency, required this.balance, required this.availableBalance, required this.status, required this.isPrimary, required this.dailyTransferLimit, required this.monthlyTransferLimit, required this.createdAt});

  factory Account.fromJson(Map<String, dynamic> json) => Account(
    id: json['id'], userId: json['user_id'], accountNumber: json['account_number'],
    iban: json['iban'], accountType: json['account_type'], currency: json['currency'],
    balance: double.parse(json['balance'].toString()),
    availableBalance: double.parse(json['available_balance'].toString()),
    status: json['status'], isPrimary: json['is_primary'],
    dailyTransferLimit: double.parse(json['daily_transfer_limit'].toString()),
    monthlyTransferLimit: double.parse(json['monthly_transfer_limit'].toString()),
    createdAt: DateTime.parse(json['created_at']),
  );
}

class Transaction {
  final String id;
  final String accountId;
  final String? toAccountId;
  final String type;
  final double amount;
  final String currency;
  final String? description;
  final String? reference;
  final String status;
  final int riskScore;
  final List<String> fraudFlags;
  final double? balanceBefore;
  final double? balanceAfter;
  final DateTime createdAt;

  const Transaction({required this.id, required this.accountId, this.toAccountId, required this.type, required this.amount, required this.currency, this.description, this.reference, required this.status, required this.riskScore, required this.fraudFlags, this.balanceBefore, this.balanceAfter, required this.createdAt});

  bool get isCredit => type == 'credit';
  bool get isDebit => type == 'debit' || type == 'transfer' || type == 'payment';

  factory Transaction.fromJson(Map<String, dynamic> json) => Transaction(
    id: json['id'], accountId: json['account_id'], toAccountId: json['to_account_id'],
    type: json['type'], amount: double.parse(json['amount'].toString()),
    currency: json['currency'], description: json['description'], reference: json['reference'],
    status: json['status'], riskScore: json['risk_score'] ?? 0,
    fraudFlags: List<String>.from(json['fraud_flags'] ?? []),
    balanceBefore: json['balance_before'] != null ? double.parse(json['balance_before'].toString()) : null,
    balanceAfter: json['balance_after'] != null ? double.parse(json['balance_after'].toString()) : null,
    createdAt: DateTime.parse(json['created_at']),
  );
}

class AuthTokens {
  final String accessToken;
  final String refreshToken;
  final String tokenType;
  final int expiresIn;

  const AuthTokens({required this.accessToken, required this.refreshToken, required this.tokenType, required this.expiresIn});

  factory AuthTokens.fromJson(Map<String, dynamic> json) => AuthTokens(
    accessToken: json['access_token'], refreshToken: json['refresh_token'],
    tokenType: json['token_type'], expiresIn: json['expires_in'],
  );
}
