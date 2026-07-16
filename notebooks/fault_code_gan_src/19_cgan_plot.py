fig, ax = plt.subplots(figsize=(8, 3))
ax.plot(c_history["loss_D"], label="D")
ax.plot(c_history["loss_G"], label="G")
ax.set_title("cGAN losses")
ax.legend()
plt.tight_layout()
plt.savefig(ART / "cgan_training_curves.png", dpi=120)
plt.show()

last_c = sorted(GEN_DIR.glob("cgan_epoch_*.png"))[-1]
print("cGAN class grid (each row ~ one class x 4 samples):", last_c)
display(Image.open(last_c))
print("Row order:", [IDX_TO_CODE[i] for i in range(N_CLASSES)])
