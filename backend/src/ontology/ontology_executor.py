import time
from typing import Dict, Any, List, Optional
from rdflib import URIRef
from .ontology_manager import OntologyManager
from .plan_mapper import PlanMapper
from .plan_validator import PlanValidator
from ..execution.screen_analyzer import ScreenAnalyzer
from ..execution.action_performer import ActionPerformer
from ..screen_recorder import ScreenRecorder


class OntologyExecutor:
    """Izvrsava korake na osnovu ontologije."""
    
    def __init__(self, slow_mode: bool = True, record_video: bool = True):
        self.ontology = OntologyManager()
        self.mapper = PlanMapper(self.ontology)
        self.validator = PlanValidator(self.ontology)
        
        self.analyzer = ScreenAnalyzer()
        self.performer = ActionPerformer(slow_mode=slow_mode)
        self.recorder = ScreenRecorder() if record_video else None
        
        self.slow_mode = slow_mode
        self.record_video = record_video
        
        print("[OntologyExecutor] Initialized")
    
    def execute_from_plan(self, plan_dict: Dict[str, Any], 
                          video_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Izvrsi plan koristeći ontologiju.
        
        Args:
            plan_dict: task_plan.json kao dict
            video_name: Ime video fajla
            
        Returns:
            Rezultati izvršavanja
        """
        results = {
            "success": False,
            "total_steps": 0,
            "successful_steps": 0,
            "failed_steps": 0,
            "steps": [],
            "video_path": None,
            "validation": None
        }
        
        # 1. Validiraj plan
        print("\n[OntologyExecutor] Validating plan...")
        validation = self.validator.get_validation_report(plan_dict)
        results["validation"] = validation
        
        if not validation["is_valid"]:
            print(f"[OntologyExecutor] Plan is not valid!")
            for error in validation["errors"]:
                print(f"Error: {error}")
            return results
        
        if validation["warnings"]:
            print("[OntologyExecutor] Warnings:")
            for warning in validation["warnings"]:
                print(f"{warning}")
        
        # 2. Mapiraj na ontologiju
        print("\n[OntologyExecutor] Mapping plan to ontology...")
        task_uri = self.mapper.map_plan_to_ontology(plan_dict)
        
        # 3. Dobij korake iz ontologije
        steps = self.mapper.get_steps_from_ontology(task_uri)
        results["total_steps"] = len(steps)
        
        print(f"[OntologyExecutor] Loaded {len(steps)} steps from ontology")
        
        # 4. Pokreni snimanje
        video_path = None
        if self.record_video and self.recorder:
            print("\n[OntologyExecutor] Starting recording...")
            if video_name is None:
                video_name = f"tutorial_{task_uri.split('_')[-1]}"
            video_path = self.recorder.start_recording(video_name)
            time.sleep(2)
        
        # 5. Izvrsi korake
        print("\n[OntologyExecutor] Starting execution...")
        time.sleep(3)
        
        try:
            for step in steps:
                step_result = self._execute_step(step)
                results["steps"].append(step_result)
                
                # Azuriraj stanje u ontologiji
                state = "completed" if step_result["success"] else "failed"
                self.mapper.update_step_state(step["uri"], state)
                
                if step_result["success"]:
                    results["successful_steps"] += 1
                else:
                    results["failed_steps"] += 1
                    
        except Exception as e:
            print(f"[OntologyExecutor] Critical error: {e}")
            
        finally:
            # 6. Zaustavi snimanje
            if self.record_video and self.recorder and self.recorder.is_recording:
                time.sleep(2)
                final_video = self.recorder.stop_recording()
                if final_video:
                    results["video_path"] = final_video
        
        # 7. Rezultat
        results["success"] = results["failed_steps"] == 0
        
        print("\n" + "=" * 60)
        print("[OntologyExecutor] Result")
        print("=" * 60)
        print(f"   Successful: {results['successful_steps']}/{results['total_steps']}")
        print(f"   Status: {'SUCCESS' if results['success'] else 'FAILURE'}")
        if results["video_path"]:
            print(f"   Video: {results['video_path']}")
        print("=" * 60)
        
        return results
    
    def _execute_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Izvrsi pojedinacni korak"""
        result = {
            "step_id": step["id"],
            "action": step["action"],
            "target": step.get("target", ""),
            "success": False,
            "error": None
        }
        
        action = step["action"]
        target = step.get("target", "")
        value = step.get("value")
        
        print(f"\n[Step {step['id']}] {action.upper()} → {target}")
        if step.get("description"):
            print(f"   {step['description']}")
        
        try:
            if action == "open_application":
                self.performer.minimize_all()
                time.sleep(1)
                success = self.performer.open_application(target)
                
            elif action == "wait":
                duration = int(value) if value else 3
                success = self.performer.wait(duration)
                
            elif action == "click":
                context = self._get_click_context(target)
                element = self.analyzer.find_element_coordinates(target, context)
                if element and element.get("found"):
                    success = self.performer.click(element["x"], element["y"])
                else:
                    print(f"Element '{target}' not found")
                    success = False
                    
            elif action == "double_click":
                element = self.analyzer.find_element_coordinates(target)
                if element and element.get("found"):
                    success = self.performer.double_click(element["x"], element["y"])
                else:
                    success = False
                    
            elif action == "right_click":
                element = self.analyzer.find_element_coordinates(target)
                if element and element.get("found"):
                    success = self.performer.right_click(element["x"], element["y"])
                else:
                    success = False
                    
            elif action == "type_text":
                if target.lower() not in ["editor", "screen", ""]:
                    element = self.analyzer.find_element_coordinates(target)
                    if element and element.get("found"):
                        self.performer.click(element["x"], element["y"])
                        time.sleep(0.3)
                
                success = self.performer.type_text_with_clipboard(value or "")
                
            elif action == "key_press":
                key = value or target
                success = self.performer.press_key(key.lower())
                
            elif action == "key_combination":
                keys = (value or target).lower().replace(" ", "").split("+")
                success = self.performer.key_combination(*keys)
                
            elif action == "scroll":
                amount = int(value) if value else -3
                success = self.performer.scroll(amount)
                
            else:
                print(f"Unknown action: {action}")
                success = False
            
            result["success"] = success
            
            if success:
                print(f"OK")
            else:
                print(f"Failed")
                
        except Exception as e:
            result["error"] = str(e)
            print(f"Error: {e}")
        
        return result
    
    def _get_click_context(self, target: str) -> str:
        """Generisi kontekst za Vision AI"""
        t = target.lower()
        
        if t in ["file", "edit", "view", "tools", "help"]:
            return f"Look for '{target}' in the TOP MENU BAR."
        elif "search" in t:
            return f"Look for a SEARCH BOX or SEARCH INPUT FIELD."
        elif "address" in t or "url" in t:
            return f"Look for the BROWSER ADDRESS BAR at the top."
        elif any(word in t for word in ["button", "next", "ok", "cancel", "create"]):
            return f"Look for a BUTTON labeled '{target}'."
        else:
            return f"Look for a clickable element labeled '{target}'."