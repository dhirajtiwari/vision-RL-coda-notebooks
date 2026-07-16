report = device_report()
print(json.dumps(report, indent=2))

device = pick_device()
print("pick_device() ->", device)

if report["cuda_available"]:
    print("OK: CUDA available for client-style training")
    # quick tensor smoke
    x = torch.randn(2, 3, device=device)
    print("tensor device:", x.device, "sum", float(x.sum()))
else:
    print("NOTE: CUDA not available in this environment.")
    print("  - Local demo: MPS/CPU is fine for the playbook.")
    print("  - Client train: use a GPU VM or docker/Dockerfile.ml with --gpus all")
    print("  - Install GPU PyTorch: https://pytorch.org (cu124 wheels etc.)")

# Client train entrypoints should use:
#   assert_cuda_for_client_train(allow_cpu_fallback=False)
try:
    d = assert_cuda_for_client_train(allow_cpu_fallback=True)
    print("assert_cuda_for_client_train(allow_cpu_fallback=True) ->", d)
except RuntimeError as exc:
    print("CUDA required failure:", exc)
