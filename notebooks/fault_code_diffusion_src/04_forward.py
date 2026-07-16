from ml.fault_code_vision.seed_render import render_lcd_panel
from torchvision.transforms import ToTensor, Normalize

img = render_lcd_panel("5E", style="lcd_dark", size=64)
x0 = Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))(ToTensor()(img)).unsqueeze(0)

device = pick_device()
sched = DiffusionSchedule(T=200, schedule="cosine", device=device)
x0 = x0.to(device)

ts = [0, 20, 50, 100, 150, 199]
fig, axes = plt.subplots(1, len(ts), figsize=(12, 2.2))
for ax, tval in zip(axes, ts):
    t = torch.tensor([tval], device=device)
    xt = sched.q_sample(x0, t)
    vis = (xt[0].detach().cpu() * 0.5 + 0.5).clamp(0, 1)
    ax.imshow(vis.permute(1, 2, 0).numpy())
    ax.set_title(f"t={tval}")
    ax.axis("off")
plt.suptitle("Forward diffusion on seed '5E'")
plt.tight_layout()
plt.savefig(ART / "forward_noise_5E.png", dpi=120)
plt.show()
