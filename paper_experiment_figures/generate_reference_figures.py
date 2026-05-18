from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


OUT = Path(__file__).resolve().parent

plt.rcParams.update(
    {
        "font.family": "serif",
        "font.serif": ["Times New Roman", "DejaVu Serif", "Times"],
        "font.size": 9,
        "axes.labelsize": 9,
        "axes.titlesize": 10,
        "legend.fontsize": 8,
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
        "figure.dpi": 180,
        "savefig.dpi": 300,
        "axes.linewidth": 0.8,
        "grid.linewidth": 0.45,
    }
)


COLORS = {
    "blue": "#2f5d8c",
    "teal": "#2a9d8f",
    "orange": "#e76f51",
    "gold": "#e9c46a",
    "gray": "#6c757d",
    "light": "#f5f7fa",
    "line": "#25313b",
    "green": "#3a7d44",
    "red": "#b84a4a",
}


def save(fig, name):
    png = OUT / f"{name}.png"
    pdf = OUT / f"{name}.pdf"
    fig.tight_layout()
    fig.savefig(png, bbox_inches="tight")
    fig.savefig(pdf, bbox_inches="tight")
    plt.close(fig)


def add_reference_note(ax):
    ax.text(
        0.995,
        -0.2,
        "Reference values only; replace with measured prototype results.",
        ha="right",
        va="top",
        transform=ax.transAxes,
        fontsize=7,
        color=COLORS["gray"],
    )


def fig_workflow():
    fig, ax = plt.subplots(figsize=(7.2, 2.35))
    ax.set_axis_off()

    steps = [
        ("FL training", "local updates\nand FedAvg"),
        ("Shard\ncheckpoints", r"$W^g$ per shard"),
        ("Coded\ncommitment", r"$\widetilde W=\Lambda W$" + "\nMerkle root"),
        ("Deletion\nrequest", r"target client $a$"),
        ("Affected-shard\nretraining", r"exclude $a$"),
        ("CSZK proof", r"$\pi_{cs},\pi_{rt}$"),
        ("Public\nverification", "accept / reject"),
    ]

    x_positions = np.linspace(0.06, 0.94, len(steps))
    y = 0.55
    w, h = 0.112, 0.42
    for i, ((title, subtitle), x) in enumerate(zip(steps, x_positions)):
        box = FancyBboxPatch(
            (x - w / 2, y - h / 2),
            w,
            h,
            boxstyle="round,pad=0.012,rounding_size=0.025",
            linewidth=0.9,
            edgecolor=COLORS["line"],
            facecolor=COLORS["light"] if i % 2 == 0 else "#ffffff",
        )
        ax.add_patch(box)
        ax.text(x, y + 0.065, title, ha="center", va="center", fontweight="bold", fontsize=8.5)
        ax.text(x, y - 0.105, subtitle, ha="center", va="center", fontsize=7.3, color=COLORS["gray"])
        if i < len(steps) - 1:
            start = (x + w / 2 + 0.008, y)
            end = (x_positions[i + 1] - w / 2 - 0.008, y)
            ax.add_patch(
                FancyArrowPatch(
                    start,
                    end,
                    arrowstyle="-|>",
                    mutation_scale=8,
                    linewidth=0.9,
                    color=COLORS["line"],
                )
            )

    ax.text(
        0.5,
        0.08,
        "Fig. 1. Prototype workflow for verifiable coded-sharding federated unlearning.",
        ha="center",
        fontsize=8,
    )
    fig.savefig(OUT / "fig1_prototype_workflow.png", bbox_inches="tight", dpi=300)
    fig.savefig(OUT / "fig1_prototype_workflow.pdf", bbox_inches="tight")
    plt.close(fig)


def fig_latency():
    schemes = ["No-unlearn", "FedEraser", "Coded FU", "Ours", "Full retrain"]
    latency = np.array([0.08, 0.9, 1.15, 1.82, 8.7])
    colors = [COLORS["gray"], COLORS["gold"], COLORS["teal"], COLORS["blue"], COLORS["orange"]]
    fig, ax = plt.subplots(figsize=(3.55, 2.55))
    ax.bar(schemes, latency, color=colors, edgecolor=COLORS["line"], linewidth=0.55)
    ax.set_ylabel("Deletion latency (normalized)")
    ax.set_ylim(0, 9.5)
    ax.grid(axis="y", alpha=0.35)
    ax.set_title("Deletion Cost Across Schemes")
    ax.tick_params(axis="x", rotation=22)
    add_reference_note(ax)
    save(fig, "fig2_deletion_latency")


def fig_proof_overhead():
    d = np.array([512, 1024, 2048, 4096])
    proving_s4 = np.array([7.5, 13.8, 27.2, 53.0])
    proving_s8 = np.array([12.4, 23.5, 45.8, 89.2])
    verify_s4 = np.array([0.18, 0.19, 0.21, 0.24])
    verify_s8 = np.array([0.21, 0.22, 0.25, 0.29])

    fig, ax1 = plt.subplots(figsize=(3.6, 2.65))
    ax1.plot(d, proving_s4, marker="o", color=COLORS["blue"], label="Prove, S=4")
    ax1.plot(d, proving_s8, marker="s", color=COLORS["teal"], label="Prove, S=8")
    ax1.set_xlabel("Checkpoint dimension d")
    ax1.set_ylabel("Proving time (s)")
    ax1.grid(alpha=0.35)

    ax2 = ax1.twinx()
    ax2.plot(d, verify_s4, marker="o", linestyle="--", color=COLORS["orange"], label="Verify, S=4")
    ax2.plot(d, verify_s8, marker="s", linestyle="--", color=COLORS["gold"], label="Verify, S=8")
    ax2.set_ylabel("Verification time (s)")
    ax2.set_ylim(0, 0.38)

    lines, labels = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines + lines2, labels + labels2, loc="upper left", frameon=True)
    ax1.set_title("Proof-System Overhead")
    add_reference_note(ax1)
    save(fig, "fig3_proof_overhead")


def fig_scalability():
    s = np.array([2, 4, 8, 16])
    retrain = np.array([5.8, 3.2, 1.85, 1.15])
    constraints = np.array([0.42, 0.81, 1.62, 3.45])

    fig, ax1 = plt.subplots(figsize=(3.6, 2.65))
    ax1.plot(s, retrain, marker="o", color=COLORS["orange"], label="Affected retraining")
    ax1.set_xlabel("Number of shards S")
    ax1.set_ylabel("Retraining time (normalized)")
    ax1.set_xticks(s)
    ax1.grid(alpha=0.35)

    ax2 = ax1.twinx()
    ax2.plot(s, constraints, marker="s", color=COLORS["blue"], label="CSZK constraints")
    ax2.set_ylabel("Constraints (million)")

    lines, labels = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines + lines2, labels + labels2, loc="center right", frameon=True)
    ax1.set_title("Shard Scalability Tradeoff")
    add_reference_note(ax1)
    save(fig, "fig4_scalability_tradeoff")


def fig_attack_rejection():
    attacks = [
        "Fake\ncheckpoint",
        "Wrong\nshard",
        "Skip\nretrain",
        "Modify\nunaffected",
        "Wrong\nrecompose",
        "State\nrollback",
        "Re-entry",
    ]
    components = ["rC open", "rS open", "pi_rt bind", "matrix rel.", "state chain", "not-del."]
    matrix = np.array(
        [
            [1, 0, 0, 0, 0, 0],
            [0, 1, 0, 1, 0, 0],
            [0, 0, 1, 1, 0, 0],
            [0, 0, 0, 1, 0, 0],
            [0, 0, 0, 1, 0, 0],
            [0, 0, 0, 0, 1, 0],
            [0, 0, 0, 0, 1, 1],
        ]
    )
    fig, ax = plt.subplots(figsize=(4.95, 2.65))
    ax.imshow(matrix, cmap="Greens", vmin=0, vmax=1, aspect="auto")
    ax.set_xticks(np.arange(len(components)))
    ax.set_yticks(np.arange(len(attacks)))
    ax.set_xticklabels(components, rotation=25, ha="right")
    ax.set_yticklabels(attacks)
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            ax.text(j, i, "Reject" if matrix[i, j] else "", ha="center", va="center", fontsize=7)
    ax.set_title("Attack-Rejection Mapping")
    ax.tick_params(length=0)
    add_reference_note(ax)
    save(fig, "fig5_attack_rejection")


if __name__ == "__main__":
    fig_workflow()
    fig_latency()
    fig_proof_overhead()
    fig_scalability()
    fig_attack_rejection()
    print(f"Saved reference figures to {OUT}")
