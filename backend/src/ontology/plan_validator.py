from typing import Dict, Any, List, Tuple
from .ontology_manager import OntologyManager


class PlanValidator:
    """Validira konzistentnost plana prema ontologiji"""
    
    def __init__(self, ontology_manager: OntologyManager = None):
        self.ontology = ontology_manager or OntologyManager()
        self.valid_actions = self.ontology.get_valid_actions()
    
    def validate_plan(self, plan: Dict[str, Any]) -> Tuple[bool, List[str], List[str]]:
        """
        Validiraj plan.
        
        Returns:
            Tuple[is_valid, errors, warnings]
        """
        errors = []
        warnings = []
        
        # Validacija strukture
        structure_errors = self._validate_structure(plan)
        errors.extend(structure_errors)
        
        if errors:
            return False, errors, warnings
        
        # Validacija koraka
        steps = plan.get("steps", [])
        
        for i, step in enumerate(steps):
            step_errors, step_warnings = self._validate_step(step, i, steps)
            errors.extend(step_errors)
            warnings.extend(step_warnings)
        
        # Validacija sekvence
        sequence_warnings = self._validate_sequence(steps)
        warnings.extend(sequence_warnings)
        
        return len(errors) == 0, errors, warnings
    
    def _validate_structure(self, plan: Dict[str, Any]) -> List[str]:
        """Validacija strukture plana"""
        errors = []
        
        if "goal" not in plan:
            errors.append("Plan must have 'goal'")
        
        if "steps" not in plan:
            errors.append("Plan must have 'steps'")
        elif not isinstance(plan["steps"], list):
            errors.append("'steps' must be a list")
        elif len(plan["steps"]) == 0:
            errors.append("Plan must have at least one step")
        
        return errors
    
    def _validate_step(self, step: Dict[str, Any], index: int, 
                       all_steps: List[Dict]) -> Tuple[List[str], List[str]]:
        """Validacija pojedinacnih koraka"""
        errors = []
        warnings = []
        step_num = index + 1
        
        # Akcija
        action = step.get("action", "")
        if not action:
            errors.append(f"Step {step_num}: Missing 'action'")
        elif action not in self.valid_actions:
            errors.append(f"Step {step_num}: Unknown action '{action}'. "
                         f"Valid actions: {', '.join(self.valid_actions)}")
        
        # Target za odredjene akcije
        actions_requiring_target = ["click", "double_click", "right_click", "type_text"]
        if action in actions_requiring_target:
            target = step.get("target", "")
            if not target or target == "screen":
                warnings.append(f"Step {step_num}: '{action}' missing specific target")
        
        # Value za type_text
        if action == "type_text":
            if not step.get("value"):
                errors.append(f"Step {step_num}: 'type_text' requires 'value'")
        
        # Value za key_press
        if action == "key_press":
            if not step.get("value") and not step.get("target"):
                errors.append(f"Step {step_num}: 'key_press' requires key name")
        
        # Value za wait
        if action == "wait":
            value = step.get("value")
            if value:
                try:
                    import re
                    numbers = re.findall(r'\d+', str(value))
                    if not numbers:
                        errors.append(f"Step {step_num}: 'wait' value must be a number")
                except:
                    errors.append(f"Step {step_num}: Invalid wait value")
        
        return errors, warnings
    
    def _validate_sequence(self, steps: List[Dict]) -> List[str]:
        """Validacija sekvence koraka"""
        warnings = []
        
        if not steps:
            return warnings
        
        # Pravilo 1: Preporuci wait nakon open_application
        for i, step in enumerate(steps):
            if step.get("action") == "open_application":
                if i + 1 < len(steps):
                    next_step = steps[i + 1]
                    if next_step.get("action") != "wait":
                        warnings.append(
                            f"Step {i + 1}: It is recommended to add 'wait' after 'open_application'"
                        )
        
        # Pravilo 2: click na YouTube video nakon pretrage
        has_youtube_search = False
        for i, step in enumerate(steps):
            if step.get("action") == "type_text":
                target = step.get("target", "").lower()
                if "search" in target:
                    has_youtube_search = True
            
            if has_youtube_search and step.get("action") == "click":
                target = step.get("target", "")
                if target:
                    # OK - ima specifican target za klik
                    pass
                else:
                    warnings.append(
                        f"Step {i + 1}: Click after search should have a specific target"
                    )
        
        return warnings
    
    def get_validation_report(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """Generisanje izvjestaja o validaciji"""
        is_valid, errors, warnings = self.validate_plan(plan)
        
        return {
            "is_valid": is_valid,
            "errors": errors,
            "warnings": warnings,
            "error_count": len(errors),
            "warning_count": len(warnings),
            "steps_count": len(plan.get("steps", [])),
            "summary": "Plan is valid" if is_valid else f"Plan has {len(errors)} errors"
        }