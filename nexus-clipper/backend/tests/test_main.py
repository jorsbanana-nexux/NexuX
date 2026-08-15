import unittest
from unittest.mock import AsyncMock

import main


class TestJobLifecycle(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        main.jobs.clear()
        main.cancel_flags.clear()
        main.active_count = 0
        main.ws.broadcast = AsyncMock()

    async def test_cancelled_queued_job_does_not_start_pipeline(self):
        job_id = "nx-queued-cancel"
        main.jobs[job_id] = {
            "job_id": job_id,
            "status": "cancelled",
            "progress": 0.0,
            "stage": "queued",
            "output_path": None,
            "error": None,
            "clips": [],
            "created_at": "",
        }
        main.cancel_flags[job_id] = True
        main.active_count = 1
        main.run_pipeline = AsyncMock()

        await main._process_job(job_id, "https://example.com/video", {})

        main.run_pipeline.assert_not_awaited()
        self.assertEqual(main.jobs[job_id]["status"], "cancelled")
        self.assertEqual(main.active_count, 0)

    async def test_running_cancellation_releases_slot_once(self):
        job_id = "nx-running-cancel"
        main.jobs[job_id] = {
            "job_id": job_id,
            "status": "queued",
            "progress": 0.0,
            "stage": "queued",
            "output_path": None,
            "error": None,
            "clips": [],
            "created_at": "",
        }
        main.cancel_flags[job_id] = False
        main.active_count = 1

        async def fake_pipeline(url, jid, progress, **kwargs):
            main.cancel_flags[jid] = True
            await progress("transcribing", 25)
            return {"status": "completed"}

        main.run_pipeline = fake_pipeline

        await main._process_job(job_id, "https://example.com/video", {})

        self.assertEqual(main.jobs[job_id]["status"], "cancelled")
        self.assertEqual(main.active_count, 0)

    async def test_webhook_is_delivered_without_entering_pipeline_kwargs(self):
        job_id = "nx-webhook"
        main.jobs[job_id] = {
            "job_id": job_id,
            "status": "queued",
            "progress": 0.0,
            "stage": "queued",
            "output_path": None,
            "error": None,
            "clips": [],
            "created_at": "",
        }
        main.cancel_flags[job_id] = False
        main.active_count = 1
        captured_kwargs = {}

        async def fake_pipeline(url, jid, progress, **kwargs):
            captured_kwargs.update(kwargs)
            return {
                "status": "completed",
                "output_path": "output/final.mp4",
                "clips": ["clip-1.mp4"],
            }

        main.run_pipeline = fake_pipeline
        main._send_webhook = AsyncMock()

        await main._process_job(
            job_id,
            "https://example.com/video",
            {"target_duration": 60},
            "https://hooks.example.test/nexus",
        )

        self.assertEqual(captured_kwargs, {"target_duration": 60})
        main._send_webhook.assert_awaited_once_with(
            "https://hooks.example.test/nexus",
            main.jobs[job_id],
        )
        self.assertEqual(main.jobs[job_id]["status"], "completed")
        self.assertEqual(main.active_count, 0)


if __name__ == "__main__":
    unittest.main()
