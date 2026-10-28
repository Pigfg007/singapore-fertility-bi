"""Run from any working directory: python /path/to/run_pipeline.py"""
from extract_data import main as extract
from run_analysis import main as analyze
from write_findings import main as findings

if __name__=='__main__':
    extract()
    analyze()
    findings()
