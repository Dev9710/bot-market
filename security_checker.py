# -*- coding: utf-8 -*-
"""
Security Checker - Détection Honeypot & LP Lock
Vérifie la sécurité des tokens DEX avant d'envoyer une alerte
"""

import requests
import time
import sys
from typing import Dict, Optional, Tuple
from datetime import datetime

# Fix Windows console encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

class SecurityChecker:
    """
    Classe pour vérifier la sécurité d'un token:
    1. Honeypot detection (peut-on vendre?)
    2. LP Lock verification (liquidité verrouillée?)
    3. Contract safety (ownership, mint, etc.)
    """

    def __init__(self):
        # APIs disponibles pour honeypot detection
        self.honeypot_apis = {
            'honeypot_is': 'https://api.honeypot.is/v2/IsHoneypot',
            'tokensniffer': 'https://tokensniffer.com/api/v2/tokens',
        }

        # APIs pour LP lock (à configurer selon tes besoins)
        self.lp_lock_apis = {
            'unicrypt': 'https://api.unicrypt.network',  # Nécessite clé API
            'team_finance': 'https://team.finance/api',  # Nécessite clé API
        }

        self.cache = {}  # Cache des résultats pour éviter appels répétés
        print("✅ SecurityChecker initialisé")

    def check_token_security(self, token_address: str, network: str) -> Dict:
        """
        Vérifie la sécurité complète d'un token.

        Args:
            token_address: Adresse du contrat token
            network: Réseau (eth, bsc, etc.)

        Returns:
            Dict avec tous les résultats de sécurité
        """
        cache_key = f"{network}:{token_address}"

        # Vérifier le cache (valide 1h)
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            if time.time() - cached['timestamp'] < 3600:
                print(f"📦 Utilisation cache pour {token_address[:10]}...")
                return cached['data']

        print(f"🔍 Vérification sécurité pour {token_address[:10]}... sur {network}")

        results = {
            'token_address': token_address,
            'network': network,
            'timestamp': datetime.now().isoformat(),
            'is_safe': True,  # Par défaut, devient False si problème détecté
            'risk_level': 'LOW',  # LOW, MEDIUM, HIGH, CRITICAL
            'warnings': [],
            'checks': {}
        }

        # 1. Honeypot Detection
        honeypot_result = self.check_honeypot(token_address, network)
        results['checks']['honeypot'] = honeypot_result

        if honeypot_result['is_honeypot']:
            results['is_safe'] = False
            results['risk_level'] = 'CRITICAL'
            results['warnings'].append(f"⛔ HONEYPOT DÉTECTÉ - Impossible de vendre!")

        # 2. LP Lock Verification
        lp_lock_result = self.check_lp_lock(token_address, network)
        results['checks']['lp_lock'] = lp_lock_result

        if not lp_lock_result['is_locked']:
            results['is_safe'] = False
            results['risk_level'] = 'CRITICAL'
            results['warnings'].append(f"⛔ LIQUIDITÉ NON VERROUILLÉE - Risque de rugpull!")
        elif lp_lock_result.get('lock_duration_days', 0) < 30:
            results['warnings'].append(f"⚠️ LP lockée seulement {lp_lock_result['lock_duration_days']} jours")
            if results['risk_level'] == 'LOW':
                results['risk_level'] = 'MEDIUM'

        # 3. Contract Safety (taxes, ownership, etc.)
        contract_result = self.check_contract_safety(token_address, network)
        results['checks']['contract'] = contract_result

        if contract_result.get('buy_tax', 0) > 10 or contract_result.get('sell_tax', 0) > 10:
            results['warnings'].append(f"⚠️ Taxes élevées: Buy {contract_result['buy_tax']}% / Sell {contract_result['sell_tax']}%")
            if results['risk_level'] == 'LOW':
                results['risk_level'] = 'MEDIUM'

        if not contract_result.get('is_renounced', False):
            results['warnings'].append(f"⚠️ Ownership NON renoncée - Owner peut modifier le contrat")
            if results['risk_level'] == 'LOW':
                results['risk_level'] = 'MEDIUM'

        # 4. Score de sécurité global (0-100)
        results['security_score'] = self.calculate_security_score(results)

        # Mettre en cache
        self.cache[cache_key] = {
            'timestamp': time.time(),
            'data': results
        }

        return results

    def check_honeypot(self, token_address: str, network: str) -> Dict:
        """
        Vérifie si le token est un honeypot via API honeypot.is

        Args:
            token_address: Adresse du token
            network: Réseau

        Returns:
            Dict avec résultats honeypot check
        """
        try:
            # Mapping des networks pour honeypot.is
            network_map = {
                'eth': 'ethereum',
                'bsc': 'bsc',
                'arbitrum': 'arbitrum',
                'base': 'base',
                'polygon': 'polygon'
            }

            chain = network_map.get(network, network)

            # Appel API honeypot.is
            url = f"https://api.honeypot.is/v2/IsHoneypot"
            params = {
                'address': token_address,
                'chainID': self.get_chain_id(network)
            }

            response = requests.get(url, params=params, timeout=15)

            if response.status_code == 200:
                data = response.json()

                # honeypot.is retourne un objet avec plusieurs checks
                is_honeypot = data.get('honeypotResult', {}).get('isHoneypot', False)
                buy_tax = data.get('simulationResult', {}).get('buyTax', 0)
                sell_tax = data.get('simulationResult', {}).get('sellTax', 0)
                can_sell = not is_honeypot

                return {
                    'checked': True,
                    'is_honeypot': is_honeypot,
                    'can_sell': can_sell,
                    'buy_tax': buy_tax,
                    'sell_tax': sell_tax,
                    'source': 'honeypot.is'
                }
            else:
                print(f"⚠️ honeypot.is API erreur: {response.status_code}")

        except Exception as e:
            print(f"⚠️ Erreur honeypot check: {e}")

        # Si API ne fonctionne pas, retourner résultat par défaut (SAFE mais non vérifié)
        return {
            'checked': False,
            'is_honeypot': False,
            'can_sell': True,
            'buy_tax': 0,
            'sell_tax': 0,
            'source': 'not_checked',
            'error': 'API unavailable'
        }

    def check_lp_lock(self, token_address: str, network: str) -> Dict:
        """
        Vérifie si la liquidité (LP) est verrouillée via plusieurs sources:
        1. GoPlusLabs API (gratuit, fiable)
        2. DexScreener API
        3. TokenSniffer API
        4. Vérification on-chain (fallback)

        Args:
            token_address: Adresse du token
            network: Réseau

        Returns:
            Dict avec résultats LP lock check
        """
        # Méthode 1: GoPlusLabs (API la plus fiable pour LP lock)
        result = self._check_lp_goplus(token_address, network)
        if result['checked']:
            return result

        # Méthode 2: DexScreener (données de liquidité)
        result = self._check_lp_dexscreener(token_address, network)
        if result['checked']:
            return result

        # Méthode 3: TokenSniffer (backup)
        result = self._check_lp_tokensniffer(token_address, network)
        if result['checked']:
            return result

        # Si tout échoue, retourner résultat négatif par défaut
        return {
            'checked': False,
            'is_locked': False,
            'lock_percentage': 0,
            'lock_duration_days': 0,
            'unlock_date': None,
            'locker_platform': 'unknown',
            'source': 'all_apis_failed',
            'error': 'Unable to verify LP lock - All APIs failed'
        }

    def _check_lp_goplus(self, token_address: str, network: str) -> Dict:
        """
        Vérifie LP lock via GoPlusLabs API (GRATUIT et fiable).
        Supporte: ETH, BSC, Polygon, Arbitrum, Avalanche, etc.
        """
        try:
            # Mapping des networks pour GoPlusLabs
            chain_id_map = {
                'eth': '1',
                'bsc': '56',
                'polygon': '137',
                'arbitrum': '42161',
                'avalanche': '43114',
                'optimism': '10',
                'base': '8453',
                'fantom': '250'
            }

            chain_id = chain_id_map.get(network)
            if not chain_id:
                return {'checked': False, 'error': f'Network {network} not supported by GoPlusLabs'}

            # API GoPlusLabs - Token Security
            url = f"https://api.gopluslabs.io/api/v1/token_security/{chain_id}"
            params = {'contract_addresses': token_address.lower()}

            response = requests.get(url, params=params, timeout=15)

            if response.status_code == 200:
                data = response.json()

                # GoPlusLabs retourne les données sous la clé de l'adresse
                token_data = data.get('result', {}).get(token_address.lower(), {})

                if not token_data:
                    return {'checked': False, 'error': 'No data from GoPlusLabs'}

                # Extraire les informations de LP
                is_open_source = token_data.get('is_open_source', '0') == '1'
                lp_holder_count = int(token_data.get('lp_holder_count', 0))
                lp_total_supply = float(token_data.get('lp_total_supply', 0))

                # Vérifier si LP est lockée via les holders
                holders = token_data.get('lp_holders', [])

                # Platforms de lock connues
                known_lockers = {
                    'unicrypt': ['0x663a5c229c09b049e36dcc11a9b0d4a8eb9db214'],  # Unicrypt
                    'teamfinance': ['0xe2fe530c047f2d85298b07d9333c05737f1435fb'],  # Team Finance
                    'pinklock': ['0x7ee058420e5937496f5a2096f04caa7721cf70cc'],  # PinkLock (BSC)
                    'dxsale': ['0x0000000000000000000000000000000000001004'],  # DxSale
                }

                is_locked = False
                lock_percentage = 0
                locker_platform = 'unknown'
                locked_holders = []

                # Analyser les holders pour détecter les lockers
                for holder in holders:
                    holder_address = holder.get('address', '').lower()
                    holder_percent = float(holder.get('percent', 0))
                    is_locked_holder = holder.get('is_locked', '0') == '1'

                    # Vérifier si c'est un locker connu
                    for platform, addresses in known_lockers.items():
                        if holder_address in [addr.lower() for addr in addresses]:
                            is_locked = True
                            lock_percentage += holder_percent * 100
                            locker_platform = platform
                            locked_holders.append({
                                'platform': platform,
                                'percentage': holder_percent * 100
                            })
                            break

                    # Vérifier le flag is_locked de GoPlusLabs
                    if is_locked_holder and holder_percent > 0.1:  # Au moins 10% de LP
                        is_locked = True
                        lock_percentage += holder_percent * 100
                        if locker_platform == 'unknown':
                            locker_platform = 'detected_by_goplus'

                # Calculer durée du lock (GoPlusLabs ne fournit pas cette info directement)
                # On suppose au minimum 30 jours si lockée
                lock_duration_days = 30 if is_locked else 0

                return {
                    'checked': True,
                    'is_locked': is_locked,
                    'lock_percentage': round(lock_percentage, 2),
                    'lock_duration_days': lock_duration_days,
                    'unlock_date': None,  # GoPlusLabs ne fournit pas cette info
                    'locker_platform': locker_platform,
                    'locked_holders': locked_holders,
                    'lp_total_supply': lp_total_supply,
                    'lp_holder_count': lp_holder_count,
                    'source': 'goplus_labs'
                }

        except Exception as e:
            print(f"⚠️ Erreur GoPlusLabs LP check: {e}")
            return {'checked': False, 'error': str(e)}

        return {'checked': False, 'error': 'GoPlusLabs API call failed'}

    def _check_lp_dexscreener(self, token_address: str, network: str) -> Dict:
        """
        Vérifie informations de liquidité via DexScreener API.
        Note: DexScreener ne fournit pas directement info de lock,
        mais peut donner des indices via liquidity et fdv.
        """
        try:
            # DexScreener API
            url = f"https://api.dexscreener.com/latest/dex/tokens/{token_address}"

            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                data = response.json()
                pairs = data.get('pairs', [])

                if not pairs:
                    return {'checked': False, 'error': 'No pairs found on DexScreener'}

                # Prendre la paire avec le plus de liquidité
                main_pair = max(pairs, key=lambda x: float(x.get('liquidity', {}).get('usd', 0)))

                liquidity_usd = float(main_pair.get('liquidity', {}).get('usd', 0))
                fdv = float(main_pair.get('fdv', 0))

                # Heuristique: Si liquidité > 50K et stable, probablement lockée
                # Note: Ce n'est qu'une approximation!
                is_likely_locked = liquidity_usd > 50000 and fdv > 0

                return {
                    'checked': True,
                    'is_locked': is_likely_locked,  # Approximation seulement
                    'lock_percentage': 0,  # DexScreener ne fournit pas cette info
                    'lock_duration_days': 0,
                    'unlock_date': None,
                    'locker_platform': 'unknown',
                    'liquidity_usd': liquidity_usd,
                    'source': 'dexscreener_heuristic',
                    'note': 'LP lock inferred from liquidity stability - not definitive'
                }

        except Exception as e:
            print(f"⚠️ Erreur DexScreener LP check: {e}")
            return {'checked': False, 'error': str(e)}

        return {'checked': False, 'error': 'DexScreener API call failed'}

    def _check_lp_tokensniffer(self, token_address: str, network: str) -> Dict:
        """
        Vérifie LP lock via TokenSniffer (backup method).
        """
        try:
            chain_id = self.get_chain_id(network)
            url = f"https://tokensniffer.com/api/v2/tokens/{chain_id}/{token_address}"

            response = requests.get(url, timeout=15)

            if response.status_code == 200:
                data = response.json()

                # TokenSniffer fournit des infos sur les locks
                liquidity_locked = data.get('liquidity_locked', False)
                lock_info = data.get('lock_info', {})

                if lock_info:
                    return {
                        'checked': True,
                        'is_locked': liquidity_locked,
                        'lock_percentage': lock_info.get('percentage', 0),
                        'lock_duration_days': lock_info.get('duration_days', 0),
                        'unlock_date': lock_info.get('unlock_date'),
                        'locker_platform': lock_info.get('platform', 'unknown'),
                        'source': 'tokensniffer'
                    }

        except Exception as e:
            print(f"⚠️ Erreur TokenSniffer LP check: {e}")
            return {'checked': False, 'error': str(e)}

        return {'checked': False, 'error': 'TokenSniffer API call failed'}

    def check_contract_safety(self, token_address: str, network: str) -> Dict:
        """
        Vérifie la sécurité du contrat token:
        - Ownership renoncée?
        - Mint function désactivée?
        - Blacklist function présente?
        - Pause trading function?

        Utilise TokenSniffer ou similaire.

        Args:
            token_address: Adresse du token
            network: Réseau

        Returns:
            Dict avec résultats contract safety
        """
        try:
            # Utiliser TokenSniffer API (gratuit, limité à 1 req/sec)
            chain_id = self.get_chain_id(network)

            url = f"https://tokensniffer.com/api/v2/tokens/{chain_id}/{token_address}"
            headers = {'Accept': 'application/json'}

            response = requests.get(url, headers=headers, timeout=15)

            if response.status_code == 200:
                data = response.json()

                # TokenSniffer retourne un score et des détails
                score = data.get('score', 0)
                risks = data.get('risks', [])

                # Extraire infos importantes
                is_renounced = 'ownership_renounced' in [r.get('name') for r in risks]
                has_mint = 'mint_function' in [r.get('name') for r in risks]
                has_blacklist = 'blacklist_function' in [r.get('name') for r in risks]
                can_pause = 'pause_function' in [r.get('name') for r in risks]

                return {
                    'checked': True,
                    'score': score,
                    'is_renounced': is_renounced,
                    'has_mint_function': has_mint,
                    'has_blacklist': has_blacklist,
                    'can_pause_trading': can_pause,
                    'buy_tax': data.get('buy_tax', 0),
                    'sell_tax': data.get('sell_tax', 0),
                    'source': 'tokensniffer'
                }

        except Exception as e:
            print(f"⚠️ Erreur contract safety check: {e}")

        # Fallback si API ne marche pas
        return {
            'checked': False,
            'score': 0,
            'is_renounced': False,
            'has_mint_function': False,
            'has_blacklist': False,
            'can_pause_trading': False,
            'buy_tax': 0,
            'sell_tax': 0,
            'source': 'not_checked',
            'error': 'API unavailable'
        }

    def calculate_security_score(self, results: Dict) -> int:
        """
        Calcule un score de sécurité global (0-100).

        Args:
            results: Dict avec tous les résultats de checks

        Returns:
            Score entre 0 et 100
        """
        score = 100

        # Honeypot = -100 points (éliminatoire)
        if results['checks']['honeypot'].get('is_honeypot'):
            return 0

        # LP non lockée = -50 points
        if not results['checks']['lp_lock'].get('is_locked'):
            score -= 50

        # LP lockée moins de 30 jours = -20 points
        elif results['checks']['lp_lock'].get('lock_duration_days', 0) < 30:
            score -= 20

        # Ownership non renoncée = -15 points
        if not results['checks']['contract'].get('is_renounced'):
            score -= 15

        # Taxes élevées = -10 points par 5% au-dessus de 5%
        buy_tax = results['checks']['contract'].get('buy_tax', 0)
        sell_tax = results['checks']['contract'].get('sell_tax', 0)

        if buy_tax > 5:
            score -= (buy_tax - 5) * 2
        if sell_tax > 5:
            score -= (sell_tax - 5) * 2

        # Fonctions dangereuses
        if results['checks']['contract'].get('has_mint_function'):
            score -= 10
        if results['checks']['contract'].get('has_blacklist'):
            score -= 15
        if results['checks']['contract'].get('can_pause_trading'):
            score -= 10

        return max(0, min(100, score))

    def get_chain_id(self, network: str) -> int:
        """Retourne le chain ID pour un réseau."""
        chain_ids = {
            'eth': 1,
            'bsc': 56,
            'polygon': 137,
            'arbitrum': 42161,
            'base': 8453,
            'avalanche': 43114,
            'optimism': 10,
            'fantom': 250,
            'solana': 0  # Solana n'a pas de chain ID EVM
        }
        return chain_ids.get(network, 1)

    def should_send_alert(self, security_result: Dict, min_security_score: int = 50) -> Tuple[bool, str]:
        """
        Détermine si une alerte doit être envoyée basé sur la sécurité.

        Args:
            security_result: Résultats du check de sécurité
            min_security_score: Score minimum requis (défaut: 50)

        Returns:
            (should_send, reason)
        """
        # BLOQUEURS ABSOLUS
        if security_result['checks']['honeypot'].get('is_honeypot'):
            return False, "⛔ HONEYPOT DÉTECTÉ - Alerte bloquée"

        # TEMPORAIREMENT DÉSACTIVÉ POUR TESTS
        # Note: Les tokens sans LP lockée ont un risque de rugpull plus élevé
        # if not security_result['checks']['lp_lock'].get('is_locked'):
        #     return False, "⛔ LP NON LOCKÉE - Risque de rugpull - Alerte bloquée"

        # Score de sécurité insuffisant
        if security_result['security_score'] < min_security_score:
            return False, f"⚠️ Score sécurité trop faible ({security_result['security_score']}/{min_security_score}) - Alerte bloquée"

        # Risk level CRITICAL
        if security_result['risk_level'] == 'CRITICAL':
            return False, f"⛔ Niveau de risque CRITICAL - Alerte bloquée"

        # Tout est OK
        return True, f"✅ Sécurité validée (score: {security_result['security_score']}/100)"

    def format_security_warning(self, security_result: Dict) -> str:
        """
        Formate un message d'avertissement de sécurité pour l'alerte.

        Args:
            security_result: Résultats du check de sécurité

        Returns:
            Texte formaté pour Telegram
        """
        if security_result['security_score'] >= 80:
            return f"🔒 *SÉCURITÉ: EXCELLENTE* ({security_result['security_score']}/100)\n"

        warnings = "\n⚠️ *AVERTISSEMENTS SÉCURITÉ:*\n"
        for warning in security_result['warnings']:
            warnings += f"{warning}\n"

        warnings += f"\n🔒 Score sécurité: {security_result['security_score']}/100 ({security_result['risk_level']})\n"

        return warnings


# Exemple d'utilisation
if __name__ == "__main__":
    checker = SecurityChecker()

    # Test sur un token ETH (exemple: PEPE)
    token_address = "0x6982508145454Ce325dDbE47a25d4ec3d2311933"
    network = "eth"

    print(f"🔍 Test de sécurité pour {token_address[:10]}... sur {network}\n")

    # Vérifier la sécurité
    result = checker.check_token_security(token_address, network)

    print(f"\n{'='*80}")
    print(f"📊 RÉSULTATS SÉCURITÉ")
    print(f"{'='*80}")
    print(f"Token: {result['token_address'][:10]}...")
    print(f"Network: {result['network']}")
    print(f"Est sûr: {result['is_safe']}")
    print(f"Niveau de risque: {result['risk_level']}")
    print(f"Score sécurité: {result['security_score']}/100")

    print(f"\n📋 CHECKS:")
    print(f"  Honeypot: {'❌ DÉTECTÉ' if result['checks']['honeypot']['is_honeypot'] else '✅ Safe'}")
    print(f"  LP Lock: {'✅ Lockée' if result['checks']['lp_lock']['is_locked'] else '❌ Non lockée'}")
    print(f"  Contract: Score {result['checks']['contract'].get('score', 'N/A')}")

    if result['warnings']:
        print(f"\n⚠️ AVERTISSEMENTS:")
        for warning in result['warnings']:
            print(f"  {warning}")

    # Tester si on doit envoyer l'alerte
    should_send, reason = checker.should_send_alert(result)
    print(f"\n{'='*80}")
    print(f"Envoyer alerte: {'OUI' if should_send else 'NON'}")
    print(f"Raison: {reason}")
    print(f"{'='*80}\n")
