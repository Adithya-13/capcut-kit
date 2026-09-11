import time
import uuid

US = 1_000_000
DRAFT_VERSION = 360000
APP_VERSION = "183.0.0"
CHECK_FLAG = 62978047
EXTRA_CATEGORIES = (
    "speeds", "placeholder_infos", "canvases",
    "sound_channel_mappings", "material_colors", "vocal_separations",
)
KEYFRAME_CATEGORIES = (
    "videos", "audios", "texts", "stickers",
    "filters", "adjusts", "handwrites", "effects",
)
MATERIAL_CATEGORIES = (
    "videos", "audios", "texts", "effects", "canvases", "material_animations",
    "placeholder_infos", "speeds", "sound_channel_mappings", "material_colors",
    "vocal_separations", "stickers", "transitions", "video_effects", "images",
    "masks", "filters", "beats", "audio_effects", "audio_fades", "adjusts",
    "loudnesses", "shapes", "hsl", "chromas", "color_curves", "digital_humans",
    "drafts", "green_screens", "handwrites", "log_color_wheels", "manual_deformations",
    "multi_language_refs", "placeholders", "plugin_effects", "primary_color_wheels",
    "realtime_denoises", "smart_crops", "smart_relights", "sound_channel_mapping",
    "tail_leaders", "text_templates", "time_marks", "video_trackings", "audio_balances",
    "audio_track_indexes", "ai_translates", "common_mask", "flowers", "material_videos",
)


def new_id() -> str:
    return str(uuid.uuid4()).upper()


def _platform() -> dict:
    return {
        "os": "mac",
        "os_version": "",
        "app_id": 359289,
        "app_version": "9.3.0",
        "app_source": "cc",
        "device_id": "",
        "hard_disk_id": "",
        "mac_address": "",
    }


def speed() -> dict:
    return {"id": new_id(), "type": "speed", "mode": 0, "speed": 1.0, "curve_speed": None}


def placeholder_info() -> dict:
    return {"id": new_id(), "type": "placeholder_info", "meta_type": "none",
            "res_path": "", "res_text": "", "error_path": "", "error_text": ""}


def canvas() -> dict:
    return {"id": new_id(), "type": "canvas_color", "color": "", "blur": 0.0, "image": "",
            "album_image": "", "image_id": "", "image_name": "", "source_platform": 0,
            "team_id": ""}


def sound_channel_mapping() -> dict:
    return {"id": new_id(), "type": "", "audio_channel_mapping": 0, "is_config_open": False}


def material_color() -> dict:
    return {"id": new_id(), "is_color_clip": False, "is_gradient": False, "solid_color": "",
            "gradient_colors": [], "gradient_percents": [], "gradient_angle": 90.0,
            "width": 0.0, "height": 0.0}


def vocal_separation() -> dict:
    return {"id": new_id(), "type": "vocal_separation", "choice": 0, "removed_sounds": [],
            "time_range": None, "production_path": "", "final_algorithm": "", "enter_from": ""}


EXTRA_BUILDERS = {
    "speeds": speed,
    "placeholder_infos": placeholder_info,
    "canvases": canvas,
    "sound_channel_mappings": sound_channel_mapping,
    "material_colors": material_color,
    "vocal_separations": vocal_separation,
}


def video_material(path: str, name: str, duration_us: int, width: int, height: int,
                   has_audio: bool) -> dict:
    return {
        "id": new_id(),
        "unique_id": "",
        "type": "video",
        "duration": duration_us,
        "path": path,
        "media_path": "",
        "local_id": "",
        "has_audio": has_audio,
        "reverse_path": "",
        "intensifies_path": "",
        "reverse_intensifies_path": "",
        "intensifies_audio_path": "",
        "cartoon_path": "",
        "width": width,
        "height": height,
        "category_id": "",
        "category_name": "",
        "material_id": "",
        "material_name": name,
        "material_url": "",
        "crop": {"upper_left_x": 0.0, "upper_left_y": 0.0, "upper_right_x": 1.0,
                 "upper_right_y": 0.0, "lower_left_x": 0.0, "lower_left_y": 1.0,
                 "lower_right_x": 1.0, "lower_right_y": 1.0},
        "crop_ratio": "free",
        "audio_fade": None,
        "crop_scale": 1.0,
        "extra_type_option": 0,
        "stable": {"stable_level": 0, "matrix_path": "",
                   "time_range": {"start": 0, "duration": 0}},
        "matting": {"flag": 0, "path": "", "interactiveTime": [], "has_use_quick_brush": False,
                    "strokes": [], "has_use_quick_eraser": False, "expansion": 0, "feather": 0,
                    "reverse": False, "custom_matting_id": "", "enable_matting_stroke": False,
                    "is_clould": False, "mask_video_path": "", "cloud_product_fps": 0.0},
        "source": 0,
        "source_platform": 0,
        "formula_id": "",
        # CapCut rejects the clip unless this bitfield matches what its own importer writes
        "check_flag": CHECK_FLAG,
        "video_algorithm": {"algorithms": [], "time_range": None, "path": "",
                            "gameplay_configs": [], "ai_in_painting_config": [],
                            "complement_frame_config": None, "motion_blur_config": None,
                            "deflicker": None, "noise_reduction": None, "quality_enhance": None,
                            "super_resolution": None, "ai_background_configs": [],
                            "smart_complement_frame": None, "aigc_generate": None,
                            "aigc_generate_list": [], "mouth_shape_driver": None,
                            "ai_expression_driven": None, "ai_motion_driven": None,
                            "image_interpretation": None,
                            "story_video_modify_video_config": {
                                "task_id": "", "is_overwrite_last_video": False,
                                "tracker_task_id": "", "generate_id": "", "generate_card_id": ""},
                            "skip_algorithm_index": []},
        "is_unified_beauty_mode": False,
        "is_set_beauty_mode": False,
        "object_locked": None,
        "smart_motion": None,
        "multi_camera_info": None,
        "freeze": None,
        "picture_from": "none",
        "picture_set_category_id": "",
        "picture_set_category_name": "",
        "team_id": "",
        "local_material_id": str(uuid.uuid4()),
        "origin_material_id": "",
        "request_id": "",
        "has_sound_separated": False,
        "is_text_edit_overdub": False,
        "is_ai_generate_content": False,
        "aigc_type": "none",
        "is_copyright": False,
        "aigc_history_id": "",
        "aigc_item_id": "",
        "local_material_from": "",
        "smart_match_info": None,
        "beauty_face_preset_infos": [],
        "beauty_body_preset_id": "",
        "beauty_face_auto_preset": {"preset_id": "", "name": "", "rate_map": "", "scene": ""},
        "beauty_face_auto_preset_infos": [],
        "beauty_body_auto_preset": None,
        "live_photo_timestamp": -1,
        "live_photo_cover_path": "",
        "content_feature_info": None,
        "corner_pin": None,
        "surface_trackings": [],
        "video_mask_stroke": {"resource_id": "", "path": "", "type": "", "color": "",
                              "size": 0.0, "alpha": 0.0, "distance": 0.0, "texture": 0.0,
                              "horizontal_shift": 0.0, "vertical_shift": 0.0},
        "video_mask_shadow": {"resource_id": "", "path": "", "color": "", "alpha": 0.0,
                              "blur": 0.0, "distance": 0.0, "angle": 0.0},
        "pre_applied_vip_materials": [],
        "workflow_node_id": "",
    }


def video_segment(material_id: str, extra_refs: list[str], source_start_us: int,
                  duration_us: int, target_start_us: int, render_index: int = 0,
                  volume: float = 1.0) -> dict:
    return {
        "id": new_id(),
        "source_timerange": {"start": source_start_us, "duration": duration_us},
        "target_timerange": {"start": target_start_us, "duration": duration_us},
        "render_timerange": {"start": 0, "duration": 0},
        "desc": "",
        "state": 0,
        "speed": 1.0,
        "is_loop": False,
        "is_tone_modify": False,
        "reverse": False,
        "intensifies_audio": False,
        "cartoon": False,
        "volume": volume,
        "last_nonzero_volume": volume if volume > 0 else 1.0,
        "clip": {"scale": {"x": 1.0, "y": 1.0}, "rotation": 0.0,
                 "transform": {"x": 0.0, "y": 0.0},
                 "flip": {"vertical": False, "horizontal": False}, "alpha": 1.0},
        "uniform_scale": {"on": True, "value": 1.0},
        "material_id": material_id,
        "extra_material_refs": extra_refs,
        "render_index": render_index,
        "keyframe_refs": [],
        "enable_lut": True,
        "enable_adjust": True,
        "enable_hsl": False,
        "visible": True,
        "group_id": "",
        "enable_color_curves": True,
        "enable_hsl_curves": True,
        "track_render_index": render_index,
        "hdr_settings": {"mode": 1, "intensity": 1.0, "nits": 1000},
        "enable_color_wheels": True,
        "track_attribute": 0,
        "is_placeholder": False,
        "template_id": "",
        "enable_smart_color_adjust": False,
        "template_scene": "default",
        "common_keyframes": [],
        "caption_info": None,
        "responsive_layout": {"enable": False, "target_follow": "", "size_layout": 0,
                              "horizontal_pos_layout": 0, "vertical_pos_layout": 0},
        "enable_color_match_adjust": False,
        "enable_color_correct_adjust": False,
        "enable_adjust_mask": False,
        "raw_segment_id": "",
        "lyric_keyframes": None,
        "enable_video_mask": True,
        "digital_human_template_group_id": "",
        "color_correct_alg_result": "",
        "source": "segmentsourcenormal",
        "enable_mask_stroke": False,
        "enable_mask_shadow": False,
        "enable_color_adjust_pro": False,
        "segment_color_tag": "",
    }


def video_track(segments: list[dict], main: bool = True) -> dict:
    return {
        "id": new_id(),
        "type": "video",
        "flag": 0 if main else 2,
        "attribute": 0,
        "name": "",
        "is_default_name": True,
        "segments": segments,
    }


def new_draft_info(name: str, width: int, height: int, fps: float = 30.0) -> dict:
    now = int(time.time())
    return {
        "id": new_id(),
        "version": DRAFT_VERSION,
        "new_version": APP_VERSION,
        "name": name,
        "duration": 0,
        "create_time": now,
        "update_time": now,
        "fps": fps,
        "is_drop_frame_timecode": False,
        "color_space": 0,
        "config": {
            "video_mute": False, "record_audio_last_index": 1, "extract_audio_last_index": 1,
            "original_sound_last_index": 1, "subtitle_recognition_id": "",
            "subtitle_taskinfo": [], "lyrics_recognition_id": "", "lyrics_taskinfo": [],
            "subtitle_sync": True, "lyrics_sync": True, "voice_change_sync": False,
            "sticker_max_index": 1, "adjust_max_index": 1, "material_save_mode": 0,
            "export_range": None, "maintrack_adsorb": True, "combination_max_index": 1,
            "attachment_info": [], "zoom_info_params": None, "system_font_list": [],
            "multi_language_mode": "none", "multi_language_main": "none",
            "multi_language_current": "none", "multi_language_list": [],
            "subtitle_keywords_config": None, "use_float_render": False,
        },
        "canvas_config": {"ratio": "original", "width": width, "height": height,
                          "background": None},
        "group_container": None,
        "keyframes": {category: [] for category in KEYFRAME_CATEGORIES},
        "keyframe_graph_list": [],
        "platform": _platform(),
        "last_modified_platform": _platform(),
        "mutable_config": None,
        "cover": None,
        "retouch_cover": None,
        "extra_info": None,
        "relationships": [],
        "mixed_track_mode_on": False,
        "render_index_track_mode_on": True,
        "free_render_index_mode_on": False,
        "static_cover_image_path": "",
        "source": "default",
        "time_marks": None,
        "path": "",
        "lyrics_effects": [],
        "uneven_animation_template_info": {"composition": "", "content": "", "order": "",
                                           "sub_template_info_list": []},
        "draft_type": "video",
        "smart_ads_info": {"page_from": "", "routine": "", "draft_url": ""},
        "function_assistant_info": {
            "smart_rec_applied": False, "fixed_rec_applied": False, "auto_adjust": False,
            "auto_adjust_segid_list": [], "color_correction": False,
            "color_correction_segid_list": [], "enhance_quality": False,
            "smooth_slow_motion": False, "deflicker_segid_list": [],
            "video_noise_segid_list": [], "enhance_quality_segid_list": [],
            "smart_segid_list": [], "retouch": False, "retouch_segid_list": [],
            "enhande_voice": False, "enhance_voice_segid_list": [],
            "audio_noise_segid_list": [], "auto_caption": False,
            "auto_caption_segid_list": [], "auto_caption_template_id": "",
            "caption_opt": False, "caption_opt_segid_list": [], "eye_correction": False,
            "eye_correction_segid_list": [], "normalize_loudness": False,
            "normalize_loudness_segid_list": [],
            "normalize_loudness_audio_denoise_segid_list": [], "auto_adjust_fixed": False,
            "auto_adjust_fixed_value": 50.0, "color_correction_fixed": False,
            "color_correction_fixed_value": 50.0, "normalize_loudness_fixed": False,
            "enhande_voice_fixed": False, "retouch_fixed": False,
            "enhance_quality_fixed": False, "smooth_slow_motion_fixed": False,
            "fps": {"num": 0, "den": 1},
        },
        "materials": {category: [] for category in MATERIAL_CATEGORIES},
        "tracks": [],
    }


def media_panel_entry(path: str, name: str, duration_us: int, width: int, height: int) -> dict:
    now_s = int(time.time())
    return {
        "ai_group_type": "", "create_time": now_s, "duration": duration_us, "enter_from": 0,
        "extra_info": name, "file_Path": path, "height": height, "id": str(uuid.uuid4()),
        "import_time": now_s, "import_time_ms": int(time.time() * US), "item_source": 1,
        "material_color_tag": "", "md5": "", "metetype": "video",
        "roughcut_time_range": {"duration": duration_us, "start": 0},
        "sub_time_range": {"duration": -1, "start": -1}, "type": 0, "width": width,
    }


def new_draft_meta(draft_id: str, name: str, folder: str, root: str) -> dict:
    now_us = int(time.time() * US)
    return {
        "cloud_draft_cover": False,
        "cloud_draft_sync": False,
        "cloud_package_completed_time": "",
        "draft_cloud_capcut_purchase_info": "",
        "draft_cloud_last_action_download": False,
        "draft_cloud_package_type": "",
        "draft_cloud_purchase_info": "",
        "draft_cloud_template_id": "",
        "draft_cloud_tutorial_info": "",
        "draft_cloud_videocut_purchase_info": "",
        "draft_cover": "draft_cover.jpg",
        "draft_deeplink_url": "",
        "draft_enterprise_info": {"draft_enterprise_extra": "", "draft_enterprise_id": "",
                                  "draft_enterprise_name": "", "enterprise_material": []},
        "draft_fold_path": folder,
        "draft_id": draft_id,
        "draft_is_ae_produce": False,
        "draft_is_ai_packaging_used": False,
        "draft_is_ai_shorts": False,
        "draft_is_ai_translate": False,
        "draft_is_article_video_draft": False,
        "draft_is_cloud_temp_draft": False,
        "draft_is_from_deeplink": "false",
        "draft_is_infinite_canvas_draft": False,
        "draft_is_invisible": False,
        "draft_is_pippit_draft": False,
        "draft_is_web_article_video": False,
        "draft_materials": [{"type": t, "value": []} for t in (0, 1, 2, 3, 6, 7)],
        "draft_materials_copied_info": [],
        "draft_name": name,
        "draft_need_rename_folder": False,
        "draft_new_version": "",
        "draft_removable_storage_device": "",
        "draft_root_path": root,
        "draft_segment_extra_info": [],
        "draft_timeline_materials_size_": 0,
        "draft_type": "",
        "draft_web_article_video_enter_from": "",
        "pippit_avatar_url": "",
        "pippit_extra_info": "",
        "pippit_id": "",
        "pippit_user_name": "",
        "tm_draft_cloud_completed": "",
        "tm_draft_cloud_entry_id": -1,
        "tm_draft_cloud_modified": 0,
        "tm_draft_cloud_parent_entry_id": -1,
        "tm_draft_cloud_space_id": -1,
        "tm_draft_cloud_user_id": -1,
        "tm_draft_create": now_us,
        "tm_draft_modified": now_us,
        "tm_draft_removed": 0,
        "tm_duration": 0,
    }
