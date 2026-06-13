export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  is_active: boolean;
  is_verified: boolean;
  kyc_status: 'pending' | 'verified' | 'rejected';
  is_2fa_enabled: boolean;
  created_at: string;
}

export interface Account {
  id: string;
  user_id: string;
  account_number: string;
  iban: string;
  account_type: string;
  currency: string;
  balance: string;
  available_balance: string;
  status: string;
  daily_transfer_limit: string;
  monthly_transfer_limit: string;
  created_at: string;
}

export interface Transaction {
  id: string;
  account_id: string;
  to_account_id: string | null;
  type: string;
  amount: string;
  currency: string;
  description: string;
  reference: string;
  status: 'completed' | 'pending' | 'flagged' | 'reversed';
  risk_score: number;
  fraud_flags: string[];
  balance_before: string;
  balance_after: string;
  created_at: string;
}

export interface DashboardStats {
  total_users: number;
  total_accounts: number;
  total_transactions: number;
  total_volume: number;
  flagged_transactions: number;
  pending_kyc: number;
}
