import re
import logging
import threading
import time
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta

from database import DatabaseManager
from models import DatabaseRecord

logger = logging.getLogger(__name__)

@dataclass
class DetectionRule:
    """Detection rule data class"""
    id: str
    name: str
    description: str
    rule_type: str  # keyword, regex, model_restriction, custom_scoring
    pattern: str
    severity: str
    points: int
    is_active: bool

class RuleCache:
    """Thread-safe rule cache with periodic refresh"""
    
    def __init__(self, refresh_interval: int = 60):  # Refresh every 60 seconds
        self._rules: List[DetectionRule] = []
        self._lock = threading.RLock()
        self._last_refresh = datetime.min
        self._refresh_interval = timedelta(seconds=refresh_interval)
        self._db_manager = DatabaseManager()
        
    def get_rules(self) -> List[DetectionRule]:
        """Get current rules, refreshing if needed"""
        with self._lock:
            now = datetime.now()
            if now - self._last_refresh > self._refresh_interval:
                self._refresh_rules()
                self._last_refresh = now
            return self._rules.copy()
    
    def _refresh_rules(self):
        """Refresh rules from database"""
        try:
            with self._db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, name, description, rule_type, pattern, severity, points, is_active
                    FROM detection_rules 
                    WHERE is_active = TRUE
                    ORDER BY severity DESC, points DESC
                """)
                
                rules = []
                for row in cursor.fetchall():
                    rule = DetectionRule(
                        id=row[0],
                        name=row[1],
                        description=row[2],
                        rule_type=row[3],
                        pattern=row[4],
                        severity=row[5],
                        points=row[6],
                        is_active=row[7]
                    )
                    rules.append(rule)
                
                self._rules = rules
                logger.debug(f"Refreshed {len(rules)} detection rules")
                
        except Exception as e:
            logger.error(f"Failed to refresh rules: {e}")

class DetectionEngine:
    """Rule-based detection engine for LLM requests"""
    
    def __init__(self, rule_refresh_interval: int = 60):
        self.rule_cache = RuleCache(rule_refresh_interval)
        
        # Compile commonly used regex patterns for performance
        self._compiled_regexes: Dict[str, re.Pattern] = {}
        
        # Statistics
        self.total_processed = 0
        self.total_flagged = 0
        self.rule_hit_count: Dict[str, int] = {}
    
    def process_batch(self, records: List[DatabaseRecord]) -> List[DatabaseRecord]:
        """Process a batch of records for detection"""
        if not records:
            return records
            
        rules = self.rule_cache.get_rules()
        if not rules:
            logger.warning("No detection rules loaded")
            return records
        
        processed_records = []
        for record in records:
            processed_record = self._process_single_record(record, rules)
            processed_records.append(processed_record)
            
        self.total_processed += len(records)
        return processed_records
    
    def _process_single_record(self, record: DatabaseRecord, rules: List[DetectionRule]) -> DatabaseRecord:
        """Process a single record against all rules"""
        total_score = 0
        triggered_rules = []
        
        # Process each rule
        for rule in rules:
            if self._check_rule(record, rule):
                total_score += rule.points
                triggered_rules.append(rule.name)
                
                # Update statistics
                self.rule_hit_count[rule.name] = self.rule_hit_count.get(rule.name, 0) + 1
        
        # Cap score at 100 and determine if flagged
        record.risk_score = min(total_score, 100)
        record.is_flagged = record.risk_score > 0
        
        if triggered_rules:
            record.flag_reason = ", ".join(triggered_rules)
            self.total_flagged += 1
            logger.info(f"Flagged request from {record.src_ip} - Score: {record.risk_score}, Rules: {record.flag_reason}")
        
        return record
    
    def _check_rule(self, record: DatabaseRecord, rule: DetectionRule) -> bool:
        """Check if a record matches a specific rule"""
        try:
            if rule.rule_type == "keyword":
                return self._check_keyword_rule(record, rule)
            elif rule.rule_type == "regex":
                return self._check_regex_rule(record, rule)
            elif rule.rule_type == "model_restriction":
                return self._check_model_restriction_rule(record, rule)
            else:
                logger.warning(f"Unknown rule type: {rule.rule_type}")
                return False
                
        except Exception as e:
            logger.error(f"Error checking rule {rule.name}: {e}")
            return False
    
    def _check_keyword_rule(self, record: DatabaseRecord, rule: DetectionRule) -> bool:
        """Check keyword rule - case insensitive substring matching"""
        if not record.prompt:
            return False
            
        # Split comma-separated keywords
        keywords = [kw.strip().lower() for kw in rule.pattern.split(',')]
        prompt_lower = record.prompt.lower()
        
        # Check if any keyword is found as substring
        for keyword in keywords:
            if keyword in prompt_lower:
                logger.debug(f"Keyword '{keyword}' found in prompt")
                return True
        
        return False
    
    def _check_regex_rule(self, record: DatabaseRecord, rule: DetectionRule) -> bool:
        """Check regex rule"""
        if not record.prompt:
            return False
        
        try:
            # Use cached compiled regex for performance
            if rule.pattern not in self._compiled_regexes:
                self._compiled_regexes[rule.pattern] = re.compile(rule.pattern, re.IGNORECASE)
            
            regex = self._compiled_regexes[rule.pattern]
            match = regex.search(record.prompt)
            
            if match:
                logger.debug(f"Regex pattern '{rule.pattern}' matched: {match.group()}")
                return True
            
        except re.error as e:
            logger.error(f"Invalid regex pattern '{rule.pattern}': {e}")
        
        return False
    
    def _check_model_restriction_rule(self, record: DatabaseRecord, rule: DetectionRule) -> bool:
        """Check if model is in restricted list"""
        if not record.model:
            return False
        
        # Split comma-separated models and check case-insensitive
        restricted_models = [model.strip().lower() for model in rule.pattern.split(',')]
        
        if record.model.lower() in restricted_models:
            logger.debug(f"Restricted model detected: {record.model}")
            return True
        
        return False
    
    
    def get_statistics(self) -> Dict:
        """Get detection engine statistics"""
        flagged_rate = (self.total_flagged / self.total_processed * 100) if self.total_processed > 0 else 0
        
        return {
            "total_processed": self.total_processed,
            "total_flagged": self.total_flagged,
            "flagged_rate_percent": round(flagged_rate, 2),
            "rule_hit_counts": self.rule_hit_count.copy(),
            "active_rules_count": len(self.rule_cache.get_rules())
        }
    
    def force_refresh_rules(self):
        """Force refresh of detection rules"""
        with self.rule_cache._lock:
            self.rule_cache._refresh_rules()
            self.rule_cache._last_refresh = datetime.now()
        logger.info("Forced refresh of detection rules")