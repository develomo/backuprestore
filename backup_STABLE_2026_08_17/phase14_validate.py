from engine.validation import Phase14Validator

if __name__ == "__main__":
    report = Phase14Validator(".").run()
    print("PHASE 14 VALIDATION TEST")
    print("ok:", report["ok"])
    print("render_executed:", report["render_executed"])
    print("final_video_created:", report["final_video_created"])
    print("report: outputs/phase14_validation_report.json")
