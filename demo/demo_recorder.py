#!/usr/bin/env python3
"""
ARCHE API Demo Recording Script
Captures comprehensive demo flow with all endpoints
Generates demo outputs and recordings for hackathon submission
"""

import json
import time
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List
import requests
from collections import defaultdict


class DemoRecorder:
    """Records ARCHE demo flow with detailed documentation."""
    
    def __init__(self, api_base_url: str = "http://127.0.0.1:8000"):
        self.api_base = api_base_url
        self.demo_output_dir = Path("demo/recordings")
        self.demo_output_dir.mkdir(parents=True, exist_ok=True)
        self.timestamp = datetime.now().isoformat()
        self.demo_results: Dict[str, Any] = {
            "timestamp": self.timestamp,
            "api_base": self.api_base,
            "endpoints": defaultdict(list),
            "pipeline_results": [],
            "performance_metrics": {},
        }
    
    def _save_response(self, endpoint: str, request: Dict, response: Dict, duration_ms: float):
        """Save endpoint request/response for documentation."""
        self.demo_results["endpoints"][endpoint].append({
            "timestamp": time.time(),
            "request": request,
            "response": response,
            "duration_ms": duration_ms,
        })
    
    def _api_call(self, method: str, endpoint: str, payload: Dict) -> tuple[Dict, float]:
        """Make API call and return response with duration."""
        url = f"{self.api_base}{endpoint}"
        start = time.perf_counter()
        
        if method == "POST":
            resp = requests.post(url, json=payload, timeout=30)
        else:
            resp = requests.get(url, timeout=30)
        
        duration = (time.perf_counter() - start) * 1000
        resp.raise_for_status()
        return resp.json(), duration
    
    def demo_01_health_check(self):
        """Demo 01: Health check."""
        print("\n🏥 Demo 01: Health Check")
        print("=" * 60)
        
        try:
            resp, duration = self._api_call("GET", "/v1/health", {})
            print(f"✓ API Health: {resp.get('status')} ({duration:.2f}ms)")
            self._save_response("/v1/health", {}, resp, duration)
            return True
        except Exception as e:
            print(f"✗ Health check failed: {e}")
            return False
    
    def demo_02_ingest_flow(self):
        """Demo 02: Data ingestion with privacy."""
        print("\n📥 Demo 02: Data Ingestion (Privacy Abstraction)")
        print("=" * 60)
        
        test_users = [
            {
                "user_token": "demo_user_alice",
                "signals": [
                    {
                        "event_type": "view",
                        "item_token": "tech_book_001",
                        "item_category": "technology",
                        "engagement_depth": 0.9,
                        "dwell_time_seconds": 45,
                    },
                    {
                        "event_type": "save",
                        "item_token": "tech_book_001",
                        "item_category": "technology",
                        "engagement_depth": 0.95,
                    },
                ]
            },
            {
                "user_token": "demo_user_bob",
                "signals": [
                    {
                        "event_type": "view",
                        "item_token": "fiction_novel_042",
                        "item_category": "fiction",
                        "engagement_depth": 0.7,
                        "dwell_time_seconds": 30,
                    },
                ]
            },
        ]
        
        ingested_users = []
        for user_data in test_users:
            user_token = user_data["user_token"]
            print(f"\n  User: {user_token}")
            
            for signal in user_data["signals"]:
                payload = {
                    "user_token": user_token,
                    "signal": signal,
                }
                
                try:
                    resp, duration = self._api_call("POST", "/v1/ingest", payload)
                    print(f"    ✓ Ingested {signal['event_type']}: "
                          f"{signal['item_token']} ({duration:.2f}ms)")
                    print(f"      Privacy mode: {resp.get('privacy_mode')}")
                    self._save_response("/v1/ingest", payload, resp, duration)
                    ingested_users.append(user_token)
                except Exception as e:
                    print(f"    ✗ Ingest failed: {e}")
        
        return ingested_users
    
    def demo_03_simulation_flow(self, users: List[str]):
        """Demo 03: Behavioral simulation."""
        print("\n🧠 Demo 03: Behavioral Simulation (Cold-Start & Warm-Start)")
        print("=" * 60)
        
        contexts = [
            {"time_bucket": "morning", "device_class": "desktop", "entry_point": "search"},
            {"time_bucket": "evening", "device_class": "mobile", "entry_point": "social"},
            {"time_bucket": "afternoon", "device_class": "tablet", "entry_point": "home"},
        ]
        
        sim_results = []
        for user in users:
            for ctx in contexts:
                payload = {
                    "user_token": user,
                    "context": ctx,
                }
                
                try:
                    resp, duration = self._api_call("POST", "/v1/simulate", payload)
                    print(f"  ✓ {user} [{ctx['time_bucket']}/{ctx['device_class']}]:")
                    print(f"    Basis: {resp.get('simulation_basis')}")
                    print(f"    Intent: {resp['behavioral_snapshot']['current_intent']}")
                    print(f"    Engagement: {resp['behavioral_snapshot']['engagement_mode']}")
                    print(f"    Duration: {duration:.2f}ms")
                    self._save_response("/v1/simulate", payload, resp, duration)
                    sim_results.append((user, resp))
                except Exception as e:
                    print(f"  ✗ Simulation failed for {user}: {e}")
        
        return sim_results
    
    def demo_04_recommendation_flow(self, users: List[str]):
        """Demo 04: Personalized recommendations."""
        print("\n🎯 Demo 04: Personalized Recommendations")
        print("=" * 60)
        
        n_values = [6, 10]
        rec_results = []
        
        for user in users:
            contexts = [
                {"time_bucket": "evening", "device_class": "mobile"},
                {"time_bucket": "morning", "device_class": "desktop"},
            ]
            
            for ctx in contexts:
                for n in n_values:
                    payload = {
                        "user_token": user,
                        "context": ctx,
                        "n": n,
                    }
                    
                    try:
                        resp, duration = self._api_call("POST", "/v1/recommend", payload)
                        num_recs = len(resp.get("recommendations", []))
                        print(f"\n  User: {user} | Context: {ctx['time_bucket']} | n={n}")
                        print(f"    ✓ Generated {num_recs} recommendations ({duration:.2f}ms)")
                        
                        # Show recommendation breakdown
                        type_counts = defaultdict(int)
                        avg_confidence = 0
                        for rec in resp.get("recommendations", []):
                            type_counts[rec["recommendation_type"]] += 1
                            avg_confidence += rec["confidence"]
                        
                        if num_recs > 0:
                            avg_confidence /= num_recs
                            print(f"    Basis: {resp.get('simulation_basis')}")
                            print(f"    Avg Confidence: {avg_confidence:.2f}")
                            print(f"    Types: {dict(type_counts)}")
                        
                        self._save_response("/v1/recommend", payload, resp, duration)
                        rec_results.append((user, resp))
                        
                        # Show first 3 recommendations
                        for i, rec in enumerate(resp.get("recommendations", [])[:3]):
                            print(f"      {i+1}. {rec['item_name']} "
                                  f"({rec['recommendation_type']}, conf={rec['confidence']:.2f})")
                    
                    except Exception as e:
                        print(f"  ✗ Recommendation failed: {e}")
        
        return rec_results
    
    def demo_05_explainability_flow(self, rec_results: List[tuple]):
        """Demo 05: Recommendation explanations."""
        print("\n💡 Demo 05: Explainability & Reasoning")
        print("=" * 60)
        
        explained = []
        for user, rec_resp in rec_results[:4]:  # Limit to 4 for demo
            if not rec_resp.get("recommendations"):
                continue
            
            for rec in rec_resp["recommendations"][:2]:  # Explain first 2 for each
                rec_id = rec["recommendation_id"]
                payload = {"recommendation_id": rec_id}
                
                try:
                    resp, duration = self._api_call("POST", "/v1/explain", payload)
                    print(f"\n  Recommendation ID: {rec_id[:8]}...")
                    print(f"    Item: {rec['item_name']}")
                    print(f"    Type: {rec['recommendation_type']}")
                    print(f"    Explanation: {resp.get('explanation', 'N/A')[:100]}...")
                    print(f"    Duration: {duration:.2f}ms")
                    self._save_response("/v1/explain", payload, resp, duration)
                    explained.append(resp)
                
                except Exception as e:
                    print(f"  ✗ Explanation failed: {e}")
        
        return explained
    
    def demo_06_end_to_end_pipeline(self):
        """Demo 06: Full end-to-end pipeline."""
        print("\n🔗 Demo 06: End-to-End Pipeline (Single User Journey)")
        print("=" * 60)
        
        user = "demo_user_complete_journey"
        
        pipeline_stages = []
        total_time = 0
        
        # Stage 1: Ingest
        print("\n  Stage 1: Data Ingestion")
        ingest_payload = {
            "user_token": user,
            "signal": {
                "event_type": "view",
                "item_token": "premium_book_xyz",
                "item_category": "premium",
                "engagement_depth": 0.85,
                "dwell_time_seconds": 60,
            },
        }
        try:
            resp, duration = self._api_call("POST", "/v1/ingest", ingest_payload)
            print(f"    ✓ Ingested signal ({duration:.2f}ms)")
            pipeline_stages.append(("ingest", duration))
            total_time += duration
        except Exception as e:
            print(f"    ✗ Failed: {e}")
            return
        
        # Stage 2: Simulate
        print("  Stage 2: Behavioral Simulation")
        sim_payload = {
            "user_token": user,
            "context": {"time_bucket": "evening", "device_class": "mobile"},
        }
        try:
            resp, duration = self._api_call("POST", "/v1/simulate", sim_payload)
            print(f"    ✓ Generated behavioral snapshot ({duration:.2f}ms)")
            pipeline_stages.append(("simulate", duration))
            total_time += duration
        except Exception as e:
            print(f"    ✗ Failed: {e}")
            return
        
        # Stage 3: Recommend
        print("  Stage 3: Personalized Recommendations")
        rec_payload = {
            "user_token": user,
            "context": {"time_bucket": "evening", "device_class": "mobile"},
            "n": 8,
        }
        try:
            resp, duration = self._api_call("POST", "/v1/recommend", rec_payload)
            num_recs = len(resp.get("recommendations", []))
            rec_id = resp["recommendations"][0]["recommendation_id"] if num_recs > 0 else None
            print(f"    ✓ Generated {num_recs} recommendations ({duration:.2f}ms)")
            pipeline_stages.append(("recommend", duration))
            total_time += duration
        except Exception as e:
            print(f"    ✗ Failed: {e}")
            return
        
        # Stage 4: Explain (top recommendation)
        print("  Stage 4: Explainability")
        if rec_id:
            exp_payload = {"recommendation_id": rec_id}
            try:
                resp, duration = self._api_call("POST", "/v1/explain", exp_payload)
                print(f"    ✓ Generated explanation ({duration:.2f}ms)")
                pipeline_stages.append(("explain", duration))
                total_time += duration
            except Exception as e:
                print(f"    ✗ Failed: {e}")
        
        # Summary
        print(f"\n  📊 Pipeline Summary:")
        for stage, duration in pipeline_stages:
            print(f"    {stage}: {duration:.2f}ms")
        print(f"    Total: {total_time:.2f}ms")
        
        self.demo_results["pipeline_results"].append({
            "user": user,
            "stages": pipeline_stages,
            "total_time_ms": total_time,
        })
    
    def demo_07_performance_summary(self):
        """Demo 07: Performance summary."""
        print("\n📈 Demo 07: Performance Summary")
        print("=" * 60)
        
        perf_summary = {}
        for endpoint, calls in self.demo_results["endpoints"].items():
            if not calls:
                continue
            
            durations = [c["duration_ms"] for c in calls]
            perf_summary[endpoint] = {
                "calls": len(calls),
                "mean_ms": sum(durations) / len(durations),
                "min_ms": min(durations),
                "max_ms": max(durations),
            }
        
        print("\n  Endpoint Performance:")
        for endpoint, metrics in perf_summary.items():
            print(f"    {endpoint}")
            print(f"      Calls: {metrics['calls']}")
            print(f"      Mean: {metrics['mean_ms']:.2f}ms")
            print(f"      Range: {metrics['min_ms']:.2f}ms - {metrics['max_ms']:.2f}ms")
        
        self.demo_results["performance_metrics"] = perf_summary
    
    def save_results(self):
        """Save all demo results to JSON."""
        output_file = self.demo_output_dir / f"demo_results_{self.timestamp.replace(':', '-')}.json"
        with open(output_file, 'w') as f:
            json.dump(self.demo_results, f, indent=2, default=str)
        print(f"\n✓ Demo results saved to {output_file}")
        return output_file
    
    def run_full_demo(self):
        """Run complete demo flow."""
        print("\n" + "=" * 60)
        print("🎬 ARCHE Hackathon Demo Recording")
        print("=" * 60)
        
        start_time = time.time()
        
        # Check API health
        if not self.demo_01_health_check():
            print("\n❌ API is not running. Start API with:")
            print("   python -m uvicorn api.main:app --host 0.0.0.0 --port 8000")
            return None
        
        # Run demo stages
        ingested_users = self.demo_02_ingest_flow()
        if not ingested_users:
            print("❌ No users ingested. Demo failed.")
            return None
        
        self.demo_03_simulation_flow(ingested_users)
        rec_results = self.demo_04_recommendation_flow(ingested_users)
        self.demo_05_explainability_flow(rec_results)
        self.demo_06_end_to_end_pipeline()
        self.demo_07_performance_summary()
        
        # Save results
        result_file = self.save_results()
        
        # Summary
        total_time = time.time() - start_time
        print("\n" + "=" * 60)
        print(f"✅ Demo completed in {total_time:.2f}s")
        print("=" * 60)
        
        return result_file


def main():
    """Main entry point."""
    import sys
    
    api_url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
    
    recorder = DemoRecorder(api_base_url=api_url)
    result_file = recorder.run_full_demo()
    
    if result_file:
        print(f"\n📁 Results saved to: {result_file}")
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
