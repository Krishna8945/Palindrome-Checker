"""
Unit Tests for Multi-Agent Orchestrator and Pipeline Execution
"""

import unittest
from core.models import UserRole
from database.db import db_instance
from agents.orchestrator import MultiAgentOrchestrator


class TestMultiAgentOrchestrator(unittest.TestCase):

    def setUp(self):
        db_instance.initialize_seed_data()
        self.orchestrator = MultiAgentOrchestrator()

    def test_pipeline_execution_dairy_optimal(self):
        batch = db_instance.get_batch("BATCH-DAIRY-101")
        hubs = db_instance.get_all_hubs()
        trace = self.orchestrator.run_pipeline_for_batch(batch, hubs)

        self.assertEqual(len(trace["stages"]), 4)
        self.assertIn("final_plan", trace)
        final_plan = trace["final_plan"]
        self.assertIsNotNone(final_plan)
        self.assertTrue(final_plan["haccp_compliant"])
        self.assertGreater(final_plan["meals_provided"], 0)
        self.assertGreater(final_plan["co2e_abated_kg"], 0)

    def test_pipeline_execution_spoiled_poultry_overridden(self):
        # BATCH-POULTRY-303 has 255 danger zone minutes -> must be blocked and diverted to biogas
        batch = db_instance.get_batch("BATCH-POULTRY-303")
        hubs = db_instance.get_all_hubs()
        trace = self.orchestrator.run_pipeline_for_batch(batch, hubs)

        final_plan = trace["final_plan"]
        self.assertIsNotNone(final_plan)
        # Verify deterministic override to biogas
        self.assertEqual(final_plan["recommended_action"], "ANAEROBIC_DIGESTION_BIOGAS")
        self.assertEqual(final_plan["meals_provided"], 0)
        self.assertFalse(final_plan["haccp_compliant"])

    def test_hitl_approval_workflow(self):
        # Pharma batch triggers HITL
        batch = db_instance.get_batch("BATCH-PHARMA-505")
        hubs = db_instance.get_all_hubs()
        trace = self.orchestrator.run_pipeline_for_batch(batch, hubs)
        plan_id = trace["final_plan"]["plan_id"]

        # Attempt approval by unauthorized role
        denied, _, msg = self.orchestrator.approve_hitl_plan(
            plan_id, "Warehouse Guy", UserRole.COLD_CHAIN_OPERATOR
        )
        self.assertFalse(denied)
        self.assertIn("Permission Denied", msg)

        # Approve by authorized Food Safety Officer
        approved, plan, msg = self.orchestrator.approve_hitl_plan(
            plan_id, "Dr. Jane Reynolds", UserRole.FOOD_SAFETY_OFFICER
        )
        self.assertTrue(approved)
        self.assertTrue(plan.hitl_approved)


if __name__ == "__main__":
    unittest.main()
