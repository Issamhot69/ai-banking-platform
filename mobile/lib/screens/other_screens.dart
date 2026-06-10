import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';
import '../config/app_theme.dart';
import '../services/api_service.dart';
import '../services/biometric_service.dart';
import '../models/models.dart';

class RegisterScreen extends StatefulWidget {
  const RegisterScreen({super.key});
  @override
  State<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends State<RegisterScreen> {
  final _formKey = GlobalKey<FormState>();
  final _emailCtrl = TextEditingController();
  final _passCtrl = TextEditingController();
  final _firstCtrl = TextEditingController();
  final _lastCtrl = TextEditingController();
  final _phoneCtrl = TextEditingController();
  bool _loading = false;

  Future<void> _register() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() => _loading = true);
    try {
      await apiService.register(email: _emailCtrl.text.trim(), password: _passCtrl.text, firstName: _firstCtrl.text.trim(), lastName: _lastCtrl.text.trim(), phone: _phoneCtrl.text.isEmpty ? null : _phoneCtrl.text);
      if (mounted) context.go('/login');
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Erreur: $e'), backgroundColor: AppColors.error));
    } finally { if (mounted) setState(() => _loading = false); }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('Créer un compte')),
    body: SingleChildScrollView(padding: const EdgeInsets.all(24), child: Form(key: _formKey, child: Column(children: [
      TextFormField(controller: _firstCtrl, decoration: const InputDecoration(labelText: 'Prénom', prefixIcon: Icon(Icons.person_outline)), validator: (v) => v?.isEmpty == true ? 'Requis' : null),
      const SizedBox(height: 16),
      TextFormField(controller: _lastCtrl, decoration: const InputDecoration(labelText: 'Nom', prefixIcon: Icon(Icons.person_outline)), validator: (v) => v?.isEmpty == true ? 'Requis' : null),
      const SizedBox(height: 16),
      TextFormField(controller: _emailCtrl, keyboardType: TextInputType.emailAddress, decoration: const InputDecoration(labelText: 'Email', prefixIcon: Icon(Icons.email_outlined)), validator: (v) => v?.isEmpty == true ? 'Requis' : null),
      const SizedBox(height: 16),
      TextFormField(controller: _phoneCtrl, keyboardType: TextInputType.phone, decoration: const InputDecoration(labelText: 'Téléphone (optionnel)', prefixIcon: Icon(Icons.phone_outlined))),
      const SizedBox(height: 16),
      TextFormField(controller: _passCtrl, obscureText: true, decoration: const InputDecoration(labelText: 'Mot de passe', prefixIcon: Icon(Icons.lock_outline)), validator: (v) => (v?.length ?? 0) < 8 ? 'Min 8 caractères' : null),
      const SizedBox(height: 32),
      ElevatedButton(onPressed: _loading ? null : _register, child: _loading ? const CircularProgressIndicator(color: Colors.white) : const Text("S'inscrire")),
    ]))),
  );
}

class BiometricScreen extends StatelessWidget {
  const BiometricScreen({super.key});
  @override
  Widget build(BuildContext context) => Scaffold(
    body: Center(child: Padding(padding: const EdgeInsets.all(32), child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
      const Icon(Icons.fingerprint, size: 100, color: AppColors.primary),
      const SizedBox(height: 24),
      const Text('Activer Face ID / Touch ID', style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold), textAlign: TextAlign.center),
      const SizedBox(height: 16),
      const Text('Connectez-vous rapidement et en sécurité', style: TextStyle(color: AppColors.textSecondary), textAlign: TextAlign.center),
      const SizedBox(height: 40),
      ElevatedButton(onPressed: () async { final auth = await biometricService.authenticate(); if (auth && context.mounted) context.go('/home'); }, child: const Text('Activer')),
      TextButton(onPressed: () => context.go('/home'), child: const Text('Plus tard', style: TextStyle(color: AppColors.textSecondary))),
    ]))),
  );
}

class AccountsScreen extends StatefulWidget {
  const AccountsScreen({super.key});
  @override
  State<AccountsScreen> createState() => _AccountsScreenState();
}

class _AccountsScreenState extends State<AccountsScreen> {
  Map<String, dynamic>? _data;
  bool _loading = true;

  @override
  void initState() { super.initState(); _load(); }

  Future<void> _load() async {
    try { final data = await apiService.getAccounts(); setState(() { _data = data; _loading = false; }); }
    catch (_) { setState(() => _loading = false); }
  }

  @override
  Widget build(BuildContext context) {
    final accounts = (_data?['accounts'] as List?)?.map((a) => Account.fromJson(a)).toList() ?? [];
    return Scaffold(
      appBar: AppBar(title: const Text('Mes Comptes'), actions: [IconButton(icon: const Icon(Icons.add_circle_outline), onPressed: () => _showCreate(context))]),
      body: _loading ? const Center(child: CircularProgressIndicator(color: AppColors.primary))
          : RefreshIndicator(onRefresh: _load, child: ListView(padding: const EdgeInsets.all(24), children: [
            Container(padding: const EdgeInsets.all(20), decoration: BoxDecoration(gradient: const LinearGradient(colors: AppColors.primaryGradient), borderRadius: BorderRadius.circular(20)), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              const Text('Solde Total', style: TextStyle(color: Colors.white70)),
              const SizedBox(height: 8),
              Text(NumberFormat.currency(symbol: '€').format(double.parse((_data?['total_balance'] ?? 0).toString())), style: const TextStyle(color: Colors.white, fontSize: 32, fontWeight: FontWeight.bold)),
              Text('${_data?['total_accounts'] ?? 0} compte(s)', style: const TextStyle(color: Colors.white60)),
            ])),
            const SizedBox(height: 24),
            ...accounts.map((a) => Container(margin: const EdgeInsets.only(bottom: 16), padding: const EdgeInsets.all(20), decoration: BoxDecoration(color: AppColors.card, borderRadius: BorderRadius.circular(20)), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Row(children: [
                Container(width: 40, height: 40, decoration: BoxDecoration(color: AppColors.primary.withOpacity(0.1), borderRadius: BorderRadius.circular(12)), child: const Icon(Icons.account_balance_wallet, color: AppColors.primary, size: 20)),
                const SizedBox(width: 12),
                Column(crossAxisAlignment: CrossAxisAlignment.start, children: [Text(a.accountType.toUpperCase(), style: const TextStyle(fontWeight: FontWeight.bold)), Text(a.accountNumber, style: const TextStyle(color: AppColors.textSecondary, fontSize: 12))]),
                const Spacer(),
                Container(padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4), decoration: BoxDecoration(color: AppColors.success.withOpacity(0.1), borderRadius: BorderRadius.circular(8)), child: Text(a.status, style: const TextStyle(color: AppColors.success, fontSize: 11))),
              ]),
              const SizedBox(height: 16),
              Text(NumberFormat.currency(symbol: '€').format(a.balance), style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold)),
              if (a.iban != null) Text('IBAN: ${a.iban}', style: const TextStyle(color: AppColors.textHint, fontSize: 12)),
            ]))),
          ])),
    );
  }

  void _showCreate(BuildContext context) => showModalBottomSheet(context: context, backgroundColor: AppColors.surface, shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(24))), builder: (_) => Padding(padding: const EdgeInsets.all(24), child: Column(mainAxisSize: MainAxisSize.min, children: [
    const Text('Créer un compte', style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
    const SizedBox(height: 16),
    ...['checking', 'savings', 'business'].map((t) => ListTile(leading: const Icon(Icons.add_circle_outline, color: AppColors.primary), title: Text(t.toUpperCase()), onTap: () async { Navigator.pop(context); try { await apiService.createAccount(t, 'EUR'); _load(); } catch (e) { if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Erreur: $e'))); } })),
  ])));
}

class TransactionsScreen extends StatelessWidget {
  const TransactionsScreen({super.key});
  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('Transactions')),
    body: const Center(child: Text('Sélectionnez un compte', style: TextStyle(color: AppColors.textSecondary))),
  );
}

class TransferScreen extends StatefulWidget {
  const TransferScreen({super.key});
  @override
  State<TransferScreen> createState() => _TransferScreenState();
}

class _TransferScreenState extends State<TransferScreen> {
  final _fromCtrl = TextEditingController();
  final _toCtrl = TextEditingController();
  final _amountCtrl = TextEditingController();
  final _descCtrl = TextEditingController();
  bool _loading = false;

  Future<void> _transfer() async {
    if (_fromCtrl.text.isEmpty || _toCtrl.text.isEmpty || _amountCtrl.text.isEmpty) return;
    setState(() => _loading = true);
    try {
      final tx = await apiService.transfer(fromAccountId: _fromCtrl.text.trim(), toAccountId: _toCtrl.text.trim(), amount: double.parse(_amountCtrl.text), description: _descCtrl.text);
      if (mounted) { ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('✅ Virement ${tx.status}!'), backgroundColor: AppColors.success)); context.go('/home'); }
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Erreur: $e'), backgroundColor: AppColors.error));
    } finally { if (mounted) setState(() => _loading = false); }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('Virement')),
    body: SingleChildScrollView(padding: const EdgeInsets.all(24), child: Column(children: [
      Container(padding: const EdgeInsets.all(20), decoration: BoxDecoration(color: AppColors.card, borderRadius: BorderRadius.circular(20)), child: Column(children: [
        TextField(controller: _fromCtrl, style: const TextStyle(color: AppColors.textPrimary), decoration: const InputDecoration(labelText: 'Compte source (ID)', prefixIcon: Icon(Icons.account_balance_wallet_outlined))),
        const SizedBox(height: 16),
        const Icon(Icons.swap_vert_rounded, color: AppColors.primary, size: 32),
        const SizedBox(height: 16),
        TextField(controller: _toCtrl, style: const TextStyle(color: AppColors.textPrimary), decoration: const InputDecoration(labelText: 'Compte destinataire (ID)', prefixIcon: Icon(Icons.send_outlined))),
      ])),
      const SizedBox(height: 16),
      Container(padding: const EdgeInsets.all(20), decoration: BoxDecoration(color: AppColors.card, borderRadius: BorderRadius.circular(20)), child: Column(children: [
        TextField(controller: _amountCtrl, keyboardType: TextInputType.number, style: const TextStyle(color: AppColors.textPrimary, fontSize: 32, fontWeight: FontWeight.bold), decoration: const InputDecoration(labelText: 'Montant (€)', prefixIcon: Icon(Icons.euro_outlined)), textAlign: TextAlign.center),
        const SizedBox(height: 16),
        TextField(controller: _descCtrl, style: const TextStyle(color: AppColors.textPrimary), decoration: const InputDecoration(labelText: 'Description', prefixIcon: Icon(Icons.note_outlined))),
      ])),
      const SizedBox(height: 32),
      ElevatedButton.icon(onPressed: _loading ? null : _transfer, icon: _loading ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2)) : const Icon(Icons.send_rounded), label: const Text('Envoyer le virement')),
    ])),
  );
}

class CardsScreen extends StatelessWidget {
  const CardsScreen({super.key});
  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('Mes Cartes')),
    body: ListView(padding: const EdgeInsets.all(24), children: [
      _card('**** **** **** 4242', 'Visa Débit', AppColors.primaryGradient, '12/26'),
      const SizedBox(height: 16),
      _card('**** **** **** 8888', 'Mastercard Gold', AppColors.goldGradient, '08/27'),
      const SizedBox(height: 24),
      const Text('Actions', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
      const SizedBox(height: 16),
      ...[['Bloquer la carte', Icons.lock_outline, AppColors.error], ['Modifier la limite', Icons.tune_rounded, AppColors.primary], ['Carte virtuelle', Icons.credit_card_outlined, AppColors.success], ['Signaler une fraude', Icons.report_outlined, AppColors.warning]].map((i) => ListTile(
        leading: Container(width: 40, height: 40, decoration: BoxDecoration(color: (i[2] as Color).withOpacity(0.1), borderRadius: BorderRadius.circular(10)), child: Icon(i[1] as IconData, color: i[2] as Color, size: 20)),
        title: Text(i[0] as String),
        trailing: const Icon(Icons.arrow_forward_ios, size: 14, color: AppColors.textSecondary),
      )),
    ]),
  );

  Widget _card(String number, String type, List<Color> gradient, String expiry) => Container(
    height: 200,
    decoration: BoxDecoration(gradient: LinearGradient(colors: gradient, begin: Alignment.topLeft, end: Alignment.bottomRight), borderRadius: BorderRadius.circular(24), boxShadow: [BoxShadow(color: gradient[0].withOpacity(0.3), blurRadius: 20, offset: const Offset(0, 10))]),
    padding: const EdgeInsets.all(24),
    child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Row(children: [Text(type, style: const TextStyle(color: Colors.white70)), const Spacer(), const Icon(Icons.credit_card, color: Colors.white70)]),
      const Spacer(),
      Text(number, style: const TextStyle(color: Colors.white, fontSize: 18, letterSpacing: 2, fontWeight: FontWeight.bold)),
      const SizedBox(height: 16),
      Row(children: [Column(crossAxisAlignment: CrossAxisAlignment.start, children: [const Text('Titulaire', style: TextStyle(color: Colors.white60, fontSize: 11)), const Text('John Doe', style: TextStyle(color: Colors.white))]), const SizedBox(width: 24), Column(crossAxisAlignment: CrossAxisAlignment.start, children: [const Text('Exp.', style: TextStyle(color: Colors.white60, fontSize: 11)), Text(expiry, style: const TextStyle(color: Colors.white))])]),
    ]),
  );
}

class AnalyticsScreen extends StatelessWidget {
  const AnalyticsScreen({super.key});
  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('Analytics')),
    body: ListView(padding: const EdgeInsets.all(24), children: [
      _stat('Total dépensé', '€3,240', Icons.trending_down, AppColors.error, '-8%'),
      const SizedBox(height: 16),
      _stat('Total reçu', '€5,000', Icons.trending_up, AppColors.success, '+12%'),
      const SizedBox(height: 24),
      const Text('Répartition', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
      const SizedBox(height: 16),
      ...[['🍕 Restauration', 0.35, AppColors.error], ['🛒 Shopping', 0.25, AppColors.primary], ['🚗 Transport', 0.20, AppColors.warning], ['🎬 Loisirs', 0.12, AppColors.info], ['💊 Santé', 0.08, AppColors.success]].map((i) => Padding(padding: const EdgeInsets.only(bottom: 16), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [Row(children: [Text(i[0] as String), const Spacer(), Text('${((i[1] as double) * 100).toInt()}%', style: const TextStyle(fontWeight: FontWeight.bold))]), const SizedBox(height: 8), ClipRRect(borderRadius: BorderRadius.circular(4), child: LinearProgressIndicator(value: i[1] as double, backgroundColor: AppColors.surfaceLight, valueColor: AlwaysStoppedAnimation(i[2] as Color), minHeight: 8))]))),
    ]),
  );

  Widget _stat(String label, String value, IconData icon, Color color, String change) => Container(
    padding: const EdgeInsets.all(20),
    decoration: BoxDecoration(color: AppColors.card, borderRadius: BorderRadius.circular(20)),
    child: Row(children: [
      Container(width: 48, height: 48, decoration: BoxDecoration(color: color.withOpacity(0.1), borderRadius: BorderRadius.circular(12)), child: Icon(icon, color: color)),
      const SizedBox(width: 16),
      Column(crossAxisAlignment: CrossAxisAlignment.start, children: [Text(label, style: const TextStyle(color: AppColors.textSecondary)), Text(value, style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold))]),
      const Spacer(),
      Text(change, style: TextStyle(color: change.startsWith('+') ? AppColors.success : AppColors.error, fontWeight: FontWeight.bold)),
    ]),
  );
}

class NotificationsScreen extends StatelessWidget {
  const NotificationsScreen({super.key});
  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('Notifications'), actions: [TextButton(onPressed: () {}, child: const Text('Tout lire', style: TextStyle(color: AppColors.primary)))]),
    body: ListView(padding: const EdgeInsets.all(16), children: [
      _notif('Paiement envoyé', '€250.00 à John Doe', Icons.send, AppColors.primary, '2m', false),
      _notif('Salaire reçu', '€2,500.00 crédité', Icons.account_balance, AppColors.success, '3h', true),
      _notif('Alerte sécurité', 'Nouvelle connexion détectée', Icons.security, AppColors.error, '1j', true),
      _notif('Offre exclusive', 'Obtenez 1.5% cashback', Icons.local_offer, AppColors.warning, '2j', true),
    ]),
  );

  Widget _notif(String title, String body, IconData icon, Color color, String time, bool read) => Container(
    margin: const EdgeInsets.only(bottom: 12),
    padding: const EdgeInsets.all(16),
    decoration: BoxDecoration(color: read ? AppColors.card : AppColors.primary.withOpacity(0.05), borderRadius: BorderRadius.circular(16), border: read ? null : Border.all(color: AppColors.primary.withOpacity(0.2))),
    child: Row(children: [
      Container(width: 48, height: 48, decoration: BoxDecoration(color: color.withOpacity(0.1), borderRadius: BorderRadius.circular(12)), child: Icon(icon, color: color, size: 22)),
      const SizedBox(width: 12),
      Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [Text(title, style: const TextStyle(fontWeight: FontWeight.w600)), Text(body, style: const TextStyle(color: AppColors.textSecondary, fontSize: 13))])),
      Column(children: [Text(time, style: const TextStyle(color: AppColors.textHint, fontSize: 11)), if (!read) Container(width: 8, height: 8, margin: const EdgeInsets.only(top: 4), decoration: const BoxDecoration(color: AppColors.primary, shape: BoxShape.circle))]),
    ]),
  );
}
