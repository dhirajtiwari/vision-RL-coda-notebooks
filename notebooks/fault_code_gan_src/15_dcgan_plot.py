fig, ax = plt.subplots(1, 2, figsize=(11, 3.5))
ax[0].plot(history["loss_D"], label="D")
ax[0].plot(history["loss_G"], label="G")
ax[0].set_title("DCGAN losses")
ax[0].legend()
ax[0].set_xlabel("log step")
ax[1].plot(history["D_x"], label="D(real)")
ax[1].plot(history["D_G_z"], label="D(fake)")
ax[1].set_title("Discriminator outputs (~0.5 = confused)")
ax[1].legend()
plt.tight_layout()
plt.savefig(ART / "dcgan_training_curves.png", dpi=120)
plt.show()

try:
    from IPython.display import display
except ImportError:
    display = lambda x: None  # noqa: E731

last = sorted(GEN_DIR.glob("dcgan_epoch_*.png"))[-1]
print("Latest DCGAN samples:", last)
display(Image.open(last))
