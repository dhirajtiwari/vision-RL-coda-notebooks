CGAN_EPOCHS = 12  # raise to 40-80 for cleaner class-conditional digits
opt_Gc = torch.optim.Adam(Gc.parameters(), lr=LR, betas=(BETA1, 0.999))
opt_Dc = torch.optim.Adam(Dc.parameters(), lr=LR, betas=(BETA1, 0.999))
c_history = {"loss_D": [], "loss_G": []}

fixed_z = torch.randn(N_CLASSES * 4, NZ, 1, 1, device=DEVICE)
fixed_y = torch.arange(N_CLASSES, device=DEVICE).repeat_interleave(4)


def train_cgan(epochs: int = CGAN_EPOCHS):
    Gc.train()
    Dc.train()
    t0 = time.time()
    for epoch in range(1, epochs + 1):
        for i, (real, labels, _codes) in enumerate(loader):
            bsz = real.size(0)
            real = real.to(DEVICE)
            labels = labels.to(DEVICE)

            Dc.zero_grad(set_to_none=True)
            loss_D_real = criterion(
                Dc(real, labels), torch.full((bsz,), REAL_LABEL, device=DEVICE)
            )
            z = torch.randn(bsz, NZ, 1, 1, device=DEVICE)
            fake_labels = (
                labels
                if random.random() < 0.7
                else torch.randint(0, N_CLASSES, (bsz,), device=DEVICE)
            )
            fake = Gc(z, fake_labels)
            loss_D_fake = criterion(
                Dc(fake.detach(), fake_labels),
                torch.full((bsz,), FAKE_LABEL, device=DEVICE),
            )
            loss_D = loss_D_real + loss_D_fake
            loss_D.backward()
            opt_Dc.step()

            Gc.zero_grad(set_to_none=True)
            z = torch.randn(bsz, NZ, 1, 1, device=DEVICE)
            gen_labels = torch.randint(0, N_CLASSES, (bsz,), device=DEVICE)
            fake = Gc(z, gen_labels)
            loss_G = criterion(
                Dc(fake, gen_labels), torch.full((bsz,), REAL_LABEL, device=DEVICE)
            )
            loss_G.backward()
            opt_Gc.step()

            if i % 20 == 0:
                c_history["loss_D"].append(loss_D.item())
                c_history["loss_G"].append(loss_G.item())

        print(
            f"[cGAN {epoch:03d}/{epochs}] loss_D={loss_D.item():.3f} loss_G={loss_G.item():.3f}"
        )

        if epoch == 1 or epoch % 5 == 0 or epoch == epochs:
            Gc.eval()
            with torch.no_grad():
                snap = Gc(fixed_z, fixed_y).cpu()
            Gc.train()
            grid = make_grid(snap, nrow=4, normalize=True, value_range=(-1, 1))
            save_image(grid, GEN_DIR / f"cgan_epoch_{epoch:03d}.png")

    torch.save(
        {
            "G": Gc.state_dict(),
            "D": Dc.state_dict(),
            "nz": NZ,
            "n_classes": N_CLASSES,
            "idx_to_code": IDX_TO_CODE,
        },
        CKPT_DIR / "cgan.pt",
    )
    print(f"cGAN done in {time.time() - t0:.1f}s -> {CKPT_DIR / 'cgan.pt'}")


train_cgan(CGAN_EPOCHS)
