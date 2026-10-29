"""
Plot Real FDA Shortage Disruption & Supply Chain Shock Recovery Curve (Figure 2 Candidate).
Extracts daily shipment dispatch volume, pharmacy inventory drawdown, and stockout spikes
for an FDA shortage-impacted pharmaceutical formulation across a 90-180 day window.
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from simulator.disruption_injector import DisruptionInjector
from simulator.event_generator import PharmaSupplyChainSimulator

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

load_dotenv()

OUTPUT_DIR = Path("docs/charts")


def generate_disruption_timeseries(sim_days: int = 90, num_pharmacies: int = 150, num_drugs: int = 50):
    """Simulates multi-month window and captures daily metrics for a disrupted drug vs control."""
    simulator = PharmaSupplyChainSimulator(
        num_pharmacies=num_pharmacies,
        num_drugs=num_drugs,
        sim_days=sim_days,
        time_dilation=0.0
    )

    # Find a drug with active disruption in injector
    target_drug_id = None
    target_drug_name = None
    for d in simulator.drugs:
        d_id = d["drug_id"]
        impact = simulator.disruption_injector.get_disruption_impact(d_id, sim_day_offset=10)
        if impact["is_disrupted"]:
            target_drug_id = d_id
            target_drug_name = d.get("brand_name", d.get("generic_name", "Disrupted Drug"))
            break

    if not target_drug_id:
        target_drug_id = simulator.drugs[0]["drug_id"]
        target_drug_name = simulator.drugs[0]["brand_name"]

    logger.info(f"Tracking disruption trajectory for target drug: {target_drug_name} ({target_drug_id}) over {sim_days} days...")

    daily_metrics = []
    for day in range(sim_days):
        stock_events, shipment_events = simulator.generate_day_events(day)
        
        # Target drug metrics
        target_stock_events = [s for s in stock_events if s["drug_id"] == target_drug_id]
        target_shipment_events = [sh for sh in shipment_events if sh["drug_id"] == target_drug_id]

        avg_stock = sum(s["current_stock"] for s in target_stock_events) / max(1, len(target_stock_events))
        stockouts = sum(1 for s in target_stock_events if s["stockout_flag"])
        dispatches = len(target_shipment_events)
        disruption_active = target_stock_events[0]["disruption_active"] if target_stock_events else False

        daily_metrics.append({
            "day": day + 1,
            "disruption_active": disruption_active,
            "avg_stock": round(avg_stock, 1),
            "stockout_count": stockouts,
            "shipment_dispatches": dispatches
        })

    return target_drug_name, target_drug_id, daily_metrics


def render_ascii_chart(drug_name: str, drug_id: str, metrics: list):
    """Renders a text-based ASCII time-series plot of the disruption dip and stockout surge."""
    print("\n" + "=" * 90)
    print(f"   FIGURE 2: REAL FDA SHORTAGE DISRUPTION & RECOVERY CURVE (PAPER CANDIDATE)   ")
    print(f"   Drug: {drug_name} ({drug_id}) | Evaluation Window: {len(metrics)} Simulated Days")
    print("=" * 90)
    print(f"{'Day':<5} | {'Status':<12} | {'Shipments':<10} | {'Avg Stock':<12} | {'Stockouts':<10} | Visualization (Stock Level)")
    print("-" * 90)

    # Sample every 3-5 days for clean display
    step = max(1, len(metrics) // 25)
    for m in metrics[::step]:
        status = "[SHORTAGE]" if m["disruption_active"] else "[NORMAL]"
        bar_len = int(m["avg_stock"] / 6.0)
        bar = "#" * bar_len
        print(f"Day {m['day']:<3} | {status:<12} | {m['shipment_dispatches']:<10} | {m['avg_stock']:<12.1f} | {m['stockout_count']:<10} | {bar}")

    print("=" * 90)


def plot_png_chart(drug_name: str, drug_id: str, metrics: list, output_file: Path):
    """Generates high-resolution publication PNG chart if matplotlib is available."""
    try:
        import matplotlib.pyplot as plt

        days = [m["day"] for m in metrics]
        shipments = [m["shipment_dispatches"] for m in metrics]
        stocks = [m["avg_stock"] for m in metrics]
        stockouts = [m["stockout_count"] for m in metrics]

        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 8), sharex=True)
        fig.suptitle(f"Real FDA Shortage Calibration: Supply Shock & Recovery Dynamics\nTarget Formulation: {drug_name} ({drug_id})", fontsize=12, fontweight="bold")

        # 1. Shipment Volume (Supply Rate)
        ax1.plot(days, shipments, color="#d32f2f", lw=2, label="Daily Shipment Dispatches")
        ax1.set_ylabel("Shipment Pings / Day", fontsize=10)
        ax1.grid(True, linestyle="--", alpha=0.5)
        ax1.legend(loc="upper right")

        # Highlight disruption window
        disrupted_days = [m["day"] for m in metrics if m["disruption_active"]]
        if disrupted_days:
            ax1.axvspan(min(disrupted_days), max(disrupted_days), color="#ffebee", alpha=0.7, label="Active FDA Shortage")
            ax2.axvspan(min(disrupted_days), max(disrupted_days), color="#ffebee", alpha=0.7)
            ax3.axvspan(min(disrupted_days), max(disrupted_days), color="#ffebee", alpha=0.7)

        # 2. Average Inventory Level
        ax2.plot(days, stocks, color="#1976d2", lw=2, label="Avg Pharmacy Stock (Units)")
        ax2.set_ylabel("Mean Inventory", fontsize=10)
        ax2.grid(True, linestyle="--", alpha=0.5)
        ax2.legend(loc="upper right")

        # 3. Stockout Incidents Surge
        ax3.bar(days, stockouts, color="#e65100", width=0.8, alpha=0.8, label="Active Pharmacy Stockouts")
        ax3.set_ylabel("Stockout Count", fontsize=10)
        ax3.set_xlabel("Simulated Timeline (Days)", fontsize=10)
        ax3.grid(True, linestyle="--", alpha=0.5)
        ax3.legend(loc="upper right")

        plt.tight_layout()
        output_file.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_file, dpi=300)
        plt.close()
        logger.info(f"Successfully saved publication chart to {output_file.resolve()}")
    except ImportError:
        logger.warning("Matplotlib not installed in current environment. ASCII visualization rendered instead.")


def main():
    parser = argparse.ArgumentParser(description="Generate FDA Shortage Disruption Curve")
    parser.add_argument("--days", type=int, default=90, help="Number of simulated days")
    parser.add_argument("--pharmacies", type=int, default=150, help="Pharmacy count")
    parser.add_argument("--drugs", type=int, default=50, help="Drug count")
    args = parser.parse_args()

    drug_name, drug_id, metrics = generate_disruption_timeseries(
        sim_days=args.days,
        num_pharmacies=args.pharmacies,
        num_drugs=args.drugs
    )

    render_ascii_chart(drug_name, drug_id, metrics)
    out_png = OUTPUT_DIR / "shortage_disruption_curve.png"
    plot_png_chart(drug_name, drug_id, metrics, out_png)


if __name__ == "__main__":
    main()

