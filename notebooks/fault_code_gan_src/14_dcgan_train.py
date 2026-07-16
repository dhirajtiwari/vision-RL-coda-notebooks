# Increase EPOCHS (e.g. 50-100) for sharper digits after first smoke run.
EPOCHS = 12
LR = 2e-4
BETA1 = 0.5  # DCGAN paper
REAL_LABEL = 0.9  # one-sided label smoothing (Salimans et al. 2016 style)
FAKE_LABEL = 0.0

criterion = nn.BCEWithLogitsLoss()
opt_G = torch.optim.Adam(G.parameters(), lr=LR, betas=(BETA1, 0.999))
opt_D = torch.optim.Adam(D.parameters(), lr=LR, betas=(BETA1, 0.999))

fixed_noise = torch.randn(64, NZ, 1, 1, device=DEVICE)
history = {"loss_D": [], "loss_G": [], "D_x": [], "D_G_z": []}


def train_dcgan(epochs: int = EPOCHS):
    G.train()
    D.train()
    t0 = time.time()
    for epoch in range(1, epochs + 1):
        for i, (real, _y, _codes) in enumerate(loader):
            bsz = real.size(0)
            real = real.to(DEVICE)

            D.zero_grad(set_to_none=True)
            label_real = torch.full((bsz,), REAL_LABEL, device=DEVICE)
            out_real = D(real)
            loss_D_real = criterion(out_real, label_real)

            noise = torch.randn(bsz, NZ, 1, 1, device=DEVICE)
            fake = G(noise)
            label_fake = torch.full((bsz,), FAKE_LABEL, device=DEVICE)
            out_fake = D(fake.detach())
            loss_D_fake = criterion(out_fake, label_fake)
            loss_D = loss_D_real + loss_D_fake
            loss_D.backward()
            opt_D.step()

            G.zero_grad(set_to_none=True)
            out_fake_for_G = D(fake)
            loss_G = criterion(out_fake_for_G, label_real)
            loss_G.backward()
            opt_G.step()

            if i % 20 == 0:
                history["loss_D"].append(loss_D.item())
                history["loss_G"].append(loss_G.item())
                history["D_x"].append(torch.sigmoid(out_real).mean().item())
                history["D_G_z"].append(torch.sigmoid(out_fake_for_G).mean().item())

        print(
            f"[{epoch:03d}/{epochs}] "
            f"loss_D={loss_D.item():.3f} loss_G={loss_G.item():.3f} "
            f"D(x)={torch.sigmoid(out_real).mean().item():.3f} "
            f"D(G(z))={torch.sigmoid(out_fake_for_G).mean().item():.3f}"
        )

        if epoch == 1 or epoch % 5 == 0 or epoch == epochs:
            G.eval()
            with torch.no_grad():
                fake_snap = G(fixed_noise).detach().cpu()
            G.train()
            grid = make_grid(fake_snap, nrow=8, normalize=True, value_range=(-1, 1))
            save_image(grid, GEN_DIR / f"dcgan_epoch_{epoch:03d}.png")

    torch.save({"G": G.state_dict(), "D": D.state_dict(), "nz": NZ}, CKPT_DIR / "dcgan.pt")
    print(f"DCGAN done in {time.time() - t0:.1f}s -> {CKPT_DIR / 'dcgan.pt'}")


train_dcgan(EPOCHS)
