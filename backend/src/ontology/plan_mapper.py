from typing import Dict, Any, Optional
from rdflib import URIRef
import uuid
from .ontology_manager import OntologyManager


class PlanMapper:
    """Mapira task_plan.json na ontologiju"""
    
    def __init__(self, ontology_manager: OntologyManager = None):
        self.ontology = ontology_manager or OntologyManager()
    
    def map_plan_to_ontology(self, plan_dict: Dict[str, Any]) -> URIRef:
        """
        Mapiraj JSON plan na ontologiju.
        
        Args:
            plan_dict: task_plan.json kao dict
            
        Returns:
            URI kreiranog Task-a
        """
        # Generisi ID
        task_id = str(uuid.uuid4())[:8]
        
        # Validacija strukture
        self._validate_plan_structure(plan_dict)
        
        # Normalizacija podataka
        normalized_plan = self._normalize_plan(plan_dict)
        
        # Dodaj u ontologiju
        task_uri = self.ontology.add_task_to_graph(task_id, normalized_plan)
        
        print(f"[PlanMapper] Mapped plan: {task_uri}")
        print(f"[PlanMapper] Step number: {len(normalized_plan.get('steps', []))}")
        
        return task_uri
    
    def _validate_plan_structure(self, plan: Dict[str, Any]):
        """Validacija da li plan ima potrebne kljuceve"""
        required_keys = ["goal", "steps"]
        
        for key in required_keys:
            if key not in plan:
                raise ValueError(f"Plan must have '{key}' key")
        
        if not isinstance(plan["steps"], list):
            raise ValueError("'steps' must be a list")
        
        if len(plan["steps"]) == 0:
            raise ValueError("Plan must have at least one step")
    
    def _normalize_plan(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """Normalizacija plana, tj standardizacija vrijednosti"""
        normalized = {
            "original_instruction": plan.get("original_instruction", ""),
            "goal": plan.get("goal", ""),
            "prerequisites": plan.get("prerequisites", []),
            "success_criteria": plan.get("success_criteria", ""),
            "steps": []
        }
        
        for i, step in enumerate(plan.get("steps", [])):
            normalized_step = self._normalize_step(step, i + 1)
            normalized["steps"].append(normalized_step)
        
        return normalized
    
    def _normalize_step(self, step: Dict[str, Any], default_id: int) -> Dict[str, Any]:
        """Normalizacija pojedinacnog koraka"""
        # Validne akcije
        valid_actions = [
            "click", "double_click", "right_click", "type_text",
            "key_press", "key_combination", "wait", "open_application",
            "close_application", "scroll", "move_mouse"
        ]
        
        action = step.get("action", "click").lower()
        if action not in valid_actions:
            print(f"[PlanMapper] WARNING: Unknown action '{action}', using 'click'")
            action = "click"
        
        # Normalizacija value
        value = step.get("value")
        if value is not None:
            value = str(value)
            
            # Izvuci broj za wait akciju
            if action == "wait":
                import re
                numbers = re.findall(r'\d+', value)
                value = numbers[0] if numbers else "4"
        
        return {
            "id": step.get("id", default_id),
            "action": action,
            "target": step.get("target", ""),
            "value": value,
            "description": step.get("description", ""),
            "expected_result": step.get("expected_result", "")
        }
    
    def get_steps_from_ontology(self, task_uri: URIRef) -> list:
        """Dobavljanje koraka za izvrsavanje iz ontologije"""
        return self.ontology.get_task_steps(task_uri)
    
    def update_step_state(self, step_uri: str, state: str):
        """Azuriranje stanja koraka u ontologiji"""
        self.ontology.update_step_state(URIRef(step_uri), state)