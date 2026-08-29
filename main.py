import sys
from pathlib import Path
from datetime import datetime

from config.settings import DB_PATH, COOLDOWN_DAYS, VIDEOS_DIR, TEMP_DIR
from src.database.history_manager import HistoryManager
from src.topic.topic_selector import TopicSelector
from src.research.research_manager import ResearchManager
from src.script.script_generator import ScriptGenerator
from src.audio.voice_generator import VoiceGenerator
from src.timeline.timeline_builder import TimelineBuilder
from src.captions.caption_generator import CaptionGenerator
from src.media.media_manager import MediaManager
from src.audio.music_manager import MusicManager
from src.video.video_builder import VideoBuilder
from src.video.video_validator import VideoValidator
from src.qa.content_qa import ContentQA
from src.qa.sync_qa import SynchronizationQA
from src.qa.pipeline_integrity import PipelineIntegrity
from src.upload.youtube_uploader import YouTubeUploader
from src.utils.logger import logger, log_step

def run_pipeline():
    """Execute full 12-step YouTube Shorts automation pipeline driven by Master Timeline."""
    print("=" * 60)
    print("AMAZING FACTS & MYSTERIES SHORTS AUTOMATION (MASTER TIMELINE ENGINE)")
    print("=" * 60)


    # Initialize persistence and QA systems
    history_mgr = HistoryManager(DB_PATH)
    content_qa = ContentQA(history_mgr)
    sync_qa = SynchronizationQA()
    video_val = VideoValidator()
    integrity = PipelineIntegrity()

    # Step 1: Topic Selection
    log_step(1, "Selecting Unique Topic")
    topic_selector = TopicSelector(history_mgr, cooldown_days=COOLDOWN_DAYS)
    topic_data = topic_selector.select_topic()
    topic_name = topic_data["topic_name"]
    category = topic_data["category"]
    print(f" -> Selected Topic: '{topic_name}' [{category}]")

    # Step 2: Research & Fact Grounding
    log_step(2, "Researching Facts")
    research_mgr = ResearchManager()
    research_data = research_mgr.research_topic(topic_name, category)
    print(f" -> Extracted {len(research_data['facts'])} facts from {len(research_data['sources'])} source(s)")

    # Step 3: Script & Title Generation
    log_step(3, "Generating Script & Titles")
    script_gen = ScriptGenerator()
    script_data = script_gen.generate_script_and_titles(research_data)
    selected_title = script_data["selected_title"]
    print(f" -> Title: '{selected_title}'")
    print(f" -> Script Word Count: {script_data['word_count']} words")

    # Step 4: Content QA Validation
    log_step(4, "Content Quality Assurance")
    is_qa_pass, qa_reason = content_qa.validate_content_package(topic_data, research_data, script_data)
    if not is_qa_pass:
        print(f" -> Content QA FAILED: {qa_reason}")
        history_mgr.record_pipeline_run(topic_name, "QA_FAILED", error_reason=qa_reason)
        raise RuntimeError(f"Pipeline stopped at Content QA: {qa_reason}")
    print(f" -> Content QA Result: PASS ({qa_reason})")

    # Step 5: Voice Narration Generation (Authoritative Audio Timing Source)
    log_step(5, "Generating Voice Narration")
    voice_gen = VoiceGenerator()
    audio_out = TEMP_DIR / "narration.mp3"
    voice_data = voice_gen.generate_voice(script_data["script_text"], audio_out)
    duration = voice_data["duration"]
    print(f" -> Voice Narration Generated ({duration:.2f}s)")
    print(f" -> [Narration] Duration: {duration:.2f} seconds")

    # Step 6: Construct Master Timeline & Word Alignment
    log_step(6, "Building Master Timeline & Word Alignment")
    timeline_builder = TimelineBuilder()
    master_timeline = timeline_builder.build_master_timeline(
        script_text=script_data["script_text"],
        topic_name=topic_name,
        total_audio_duration=duration,
        boundary_events=voice_data.get("boundary_events", [])
    )
    words = master_timeline["words"]
    caption_groups = master_timeline["caption_groups"]
    timeline_scenes = master_timeline["scenes"]

    print(f" -> [Alignment] Words aligned: {len(words)}")
    if words:
        print(f" -> [Alignment] First word start: {words[0]['start']:.2f}s | Last word end: {words[-1]['end']:.2f}s")
    print(f" -> [Captions] Groups created: {len(caption_groups)} (Avg words/group: {len(words)/float(max(1, len(caption_groups))):.1f})")

    print(" -> [Visual Timeline]")
    for sc in timeline_scenes:
        print(f"     Scene {sc['scene_number']}: {sc['start']:.2f}s -> {sc['end']:.2f}s ({sc['duration']:.2f}s) | Query: '{sc['visual_concept']}'")

    # Step 7: Karaoke Subtitles Generation
    log_step(7, "Generating Karaoke ASS Subtitles")
    caption_gen = CaptionGenerator()
    ass_out = TEMP_DIR / "captions.ass"
    caption_meta = caption_gen.generate_karaoke_ass_captions(master_timeline, ass_out)
    print(f" -> Karaoke ASS Subtitles Built: {ass_out.name} ({caption_meta['event_count']} animated word events)")

    # Step 8: Sourcing Synchronized Visual Media
    log_step(8, "Sourcing Visuals for Master Timeline Scenes")
    media_mgr = MediaManager()
    sourced_scenes = media_mgr.source_scene_visuals(timeline_scenes, topic_name)
    print(f" -> Sourced visuals for {len(sourced_scenes)} synchronized scenes")

    # Step 9: Background Music
    log_step(9, "Selecting Background Music")
    music_mgr = MusicManager()
    music_info = music_mgr.select_background_music()

    # Step 10: FFmpeg Synchronized Video Assembly
    log_step(10, "Building Synchronized 1080x1920 Video")
    builder = VideoBuilder()
    timestamp_slug = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_filename = f"short_{timestamp_slug}.mp4"

    video_path = builder.build_short_video(
        topic_name=topic_name,
        scenes=sourced_scenes,
        narration_path=Path(voice_data["audio_path"]),
        narration_duration=duration,
        caption_path=ass_out,
        music_info=music_info,
        output_filename=out_filename
    )
    print(f" -> Video Exported: {video_path.resolve()}")

    # Step 11: Final Video QA & Synchronization QA
    log_step(11, "Synchronization & Video QA Validation")
    is_vid_valid, vid_reason, vid_info = video_val.validate_video(video_path)
    if not is_vid_valid:
        print(f" -> Video QA FAILED: {vid_reason}")
        history_mgr.record_pipeline_run(topic_name, "VIDEO_QA_FAILED", error_reason=vid_reason)
        raise RuntimeError(vid_reason)

    is_sync_valid, sync_reason, sync_metrics = sync_qa.validate_timeline_and_sync(master_timeline, vid_info["duration"])
    if not is_sync_valid:
        print(f" -> Synchronization QA FAILED: {sync_reason}")
        history_mgr.record_pipeline_run(topic_name, "SYNC_QA_FAILED", error_reason=sync_reason)
        raise RuntimeError(sync_reason)

    print(f" -> [Video QA] Narration: {duration:.2f}s | Video: {vid_info['duration']:.2f}s | Diff: {sync_metrics['difference']:.2f}s | SYNC PASS")

    # Record Topic Usage in History DB ONLY after successful production output
    topic_id = history_mgr.record_topic_usage(
        topic_name=topic_name,
        category=category,
        script_text=script_data["script_text"],
        title=selected_title,
        hook=script_data["hook"]
    )
    print(f" -> Topic Usage Recorded in Database (ID: {topic_id})")

    # Step 12: Uploading to YouTube
    log_step(12, "Uploading to YouTube")
    uploader = YouTubeUploader()

    sources_text = "\n".join([
        f"- {s['title']}: {s['url']}" if isinstance(s, dict) else f"- {s}"
        for s in research_data.get("sources", [])
    ])
    description = (
        f"{script_data.get('hook', '')}\n\n"
        f"{script_data.get('script_text', '')}\n\n"
        f"Sources & Grounding:\n{sources_text}\n\n"
        f"#Shorts #{category.replace(' ', '')} #{topic_name.replace(' ', '')} #Facts #Science #DidYouKnow"
    )
    tags = [category, topic_name, "Shorts", "Facts", "Did You Know", "Science", "Mysteries"]

    upload_result = uploader.upload_video(
        video_path=video_path,
        title=selected_title,
        description=description,
        tags=tags,
        privacy_status="private"
    )

    yt_video_id = upload_result.get("video_id", "")
    yt_url = upload_result.get("url", "")
    yt_status = upload_result.get("status", "")
    print(f" -> YouTube Upload Status: {yt_status} | URL: {yt_url}")

    # Save Metadata and Pipeline Report
    run_report_data = {
        "topic": topic_name,
        "category": category,
        "selected_title": selected_title,
        "word_count": script_data["word_count"],
        "narration_duration": duration,
        "video_duration": vid_info["duration"],
        "sync_difference": sync_metrics["difference"],
        "video_path": str(video_path.resolve()),
        "youtube_video_id": yt_video_id,
        "youtube_url": yt_url,
        "youtube_upload_status": yt_status,
        "sources": research_data["sources"],
        "scenes": sourced_scenes,
        "word_count_aligned": len(words),
        "caption_groups": caption_groups,
        "provider_health": media_mgr.health_manager.health_state
    }
    meta_file, report_file = integrity.save_run_report(run_report_data, status="SUCCESS")
    history_mgr.record_pipeline_run(
        topic_name,
        "SUCCESS",
        video_path=str(video_path.resolve()),
        youtube_video_id=yt_video_id,
        youtube_url=yt_url,
        metadata=run_report_data
    )

    print("\n" + "=" * 60)
    print("SUCCESS — SYNCHRONIZED PIPELINE COMPLETED")
    print(f"Output Video:    {video_path.resolve()}")
    print(f"YouTube URL:     {yt_url} ({yt_status})")
    print(f"Metadata JSON:   {meta_file.resolve()}")
    print(f"Report MD:       {report_file.resolve()}")
    print(f"Narration:       {duration:.2f}s | Video: {vid_info['duration']:.2f}s | Diff: {sync_metrics['difference']:.2f}s")
    print(f"Aligned Words:   {len(words)} | Caption Groups: {len(caption_groups)}")
    print("=" * 60)


if __name__ == "__main__":
    try:
        run_pipeline()
    except Exception as e:
        logger.error(f"Pipeline Execution Failed: {e}", exc_info=True)
        sys.exit(1)
