import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../config/app_theme.dart';
import '../../services/api_service.dart';
import '../../services/biometric_service.dart';

class LoginScreen extends ConsumerStatefulWidget {
  const LoginScreen({super.key});
  @override
  ConsumerState<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends ConsumerState<LoginScreen> {
  final _emailCtrl = TextEditingController();
  final _passCtrl = TextEditingController();
  final _formKey = GlobalKey<FormState>();
  bool _isLoading = false;
  bool _obscure = true;
  bool _biometricAvailable = false;

  @override
  void initState() { super.initState(); _checkBiometric(); }

  Future<void> _checkBiometric() async {
    final available = await biometricService.isAvailable();
    setState(() => _biometricAvailable = available);
  }

  Future<void> _login() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() => _isLoading = true);
    try {
      await apiService.login(_emailCtrl.text.trim(), _passCtrl.text);
      if (mounted) context.go('/home');
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Erreur: $e'), backgroundColor: AppColors.error));
    } finally { if (mounted) setState(() => _isLoading = false); }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    body: SafeArea(
      child: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: Form(
          key: _formKey,
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            const SizedBox(height: 40),
            Container(width: 60, height: 60, decoration: BoxDecoration(gradient: const LinearGradient(colors: AppColors.primaryGradient), borderRadius: BorderRadius.circular(16)), child: const Icon(Icons.account_balance, color: Colors.white, size: 32)),
            const SizedBox(height: 32),
            const Text('Bon retour 👋', style: TextStyle(fontSize: 28, fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            const Text('Connectez-vous à votre compte', style: TextStyle(color: AppColors.textSecondary, fontSize: 16)),
            const SizedBox(height: 40),
            TextFormField(controller: _emailCtrl, keyboardType: TextInputType.emailAddress, style: const TextStyle(color: AppColors.textPrimary), decoration: const InputDecoration(labelText: 'Email', prefixIcon: Icon(Icons.email_outlined, color: AppColors.textSecondary)), validator: (v) => v?.isEmpty == true ? 'Email requis' : null),
            const SizedBox(height: 16),
            TextFormField(controller: _passCtrl, obscureText: _obscure, style: const TextStyle(color: AppColors.textPrimary), decoration: InputDecoration(labelText: 'Mot de passe', prefixIcon: const Icon(Icons.lock_outline, color: AppColors.textSecondary), suffixIcon: IconButton(icon: Icon(_obscure ? Icons.visibility_off : Icons.visibility, color: AppColors.textSecondary), onPressed: () => setState(() => _obscure = !_obscure))), validator: (v) => v?.isEmpty == true ? 'Requis' : null),
            const SizedBox(height: 32),
            ElevatedButton(onPressed: _isLoading ? null : _login, child: _isLoading ? const SizedBox(height: 20, width: 20, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2)) : const Text('Se connecter')),
            const SizedBox(height: 16),
            if (_biometricAvailable) OutlinedButton.icon(
              onPressed: () async { final auth = await biometricService.authenticate(); if (auth && mounted) context.go('/home'); },
              icon: const Icon(Icons.fingerprint, color: AppColors.primary),
              label: const Text('Connexion biométrique', style: TextStyle(color: AppColors.primary)),
              style: OutlinedButton.styleFrom(minimumSize: const Size(double.infinity, 56), side: const BorderSide(color: AppColors.primary), shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16))),
            ),
            const SizedBox(height: 24),
            Row(mainAxisAlignment: MainAxisAlignment.center, children: [
              const Text("Pas de compte ? ", style: TextStyle(color: AppColors.textSecondary)),
              GestureDetector(onTap: () => context.go('/register'), child: const Text('Créer un compte', style: TextStyle(color: AppColors.primary, fontWeight: FontWeight.w600))),
            ]),
          ]),
        ),
      ),
    ),
  );
}
