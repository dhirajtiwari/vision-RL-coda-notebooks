class CondGenerator(nn.Module):
    def __init__(
        self,
        n_classes: int = N_CLASSES,
        nz: int = NZ,
        ngf: int = NGF,
        nc: int = NC,
        emb_dim: int = 50,
    ):
        super().__init__()
        self.label_emb = nn.Embedding(n_classes, emb_dim)
        self.net = nn.Sequential(
            nn.ConvTranspose2d(nz + emb_dim, ngf * 8, 4, 1, 0, bias=False),
            nn.BatchNorm2d(ngf * 8),
            nn.ReLU(True),
            nn.ConvTranspose2d(ngf * 8, ngf * 4, 4, 2, 1, bias=False),
            nn.BatchNorm2d(ngf * 4),
            nn.ReLU(True),
            nn.ConvTranspose2d(ngf * 4, ngf * 2, 4, 2, 1, bias=False),
            nn.BatchNorm2d(ngf * 2),
            nn.ReLU(True),
            nn.ConvTranspose2d(ngf * 2, ngf, 4, 2, 1, bias=False),
            nn.BatchNorm2d(ngf),
            nn.ReLU(True),
            nn.ConvTranspose2d(ngf, nc, 4, 2, 1, bias=False),
            nn.Tanh(),
        )

    def forward(self, z: torch.Tensor, labels: torch.Tensor) -> torch.Tensor:
        emb = self.label_emb(labels).unsqueeze(2).unsqueeze(3)
        x = torch.cat([z, emb], dim=1)
        return self.net(x)


class CondDiscriminator(nn.Module):
    def __init__(
        self,
        n_classes: int = N_CLASSES,
        ndf: int = NDF,
        nc: int = NC,
        emb_dim: int = 50,
    ):
        super().__init__()
        self.label_emb = nn.Embedding(n_classes, emb_dim)
        self.emb_dim = emb_dim
        self.net = nn.Sequential(
            nn.Conv2d(nc + emb_dim, ndf, 4, 2, 1, bias=False),
            nn.LeakyReLU(0.2, inplace=True),
            nn.Conv2d(ndf, ndf * 2, 4, 2, 1, bias=False),
            nn.BatchNorm2d(ndf * 2),
            nn.LeakyReLU(0.2, inplace=True),
            nn.Conv2d(ndf * 2, ndf * 4, 4, 2, 1, bias=False),
            nn.BatchNorm2d(ndf * 4),
            nn.LeakyReLU(0.2, inplace=True),
            nn.Conv2d(ndf * 4, ndf * 8, 4, 2, 1, bias=False),
            nn.BatchNorm2d(ndf * 8),
            nn.LeakyReLU(0.2, inplace=True),
            nn.Conv2d(ndf * 8, 1, 4, 1, 0, bias=False),
        )

    def forward(self, x: torch.Tensor, labels: torch.Tensor) -> torch.Tensor:
        b, _, h, w = x.shape
        emb = self.label_emb(labels)
        emb_map = emb.unsqueeze(2).unsqueeze(3).expand(b, self.emb_dim, h, w)
        x = torch.cat([x, emb_map], dim=1)
        return self.net(x).view(-1)


Gc = CondGenerator().to(DEVICE)
Dc = CondDiscriminator().to(DEVICE)
Gc.apply(weights_init)
Dc.apply(weights_init)
print(f"cGAN G params: {sum(p.numel() for p in Gc.parameters()):,}")
print(f"cGAN D params: {sum(p.numel() for p in Dc.parameters()):,}")
