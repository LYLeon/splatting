import torch
import timeit
import sys

sys.path.append(".")


def run_test_forward(method, batch_size, spatial_size, flow_init, repetitions=10):
    frame = torch.ones(batch_size, 3, spatial_size, spatial_size)
    if flow_init == "zeros":
        flow = torch.zeros(batch_size, 2, spatial_size, spatial_size)
    elif flow_init == "ones":
        flow = torch.ones(batch_size, 2, spatial_size, spatial_size)
    else:
        raise NotImplementedError
    if method == "splatting_cpp":
        import splatting_cpp

        output = torch.zeros_like(frame)

        def test_fn():
            splatting_cpp.splatting_forward_cpu(frame, flow, output)

    elif method == "splatting_function":
        import splatting

        def test_fn():
            splatting.SummationSplattingFunction.apply(frame, flow)

    elif method == "splatting_function_summation":
        import splatting

        def test_fn():
            splatting.splatting_function("summation", frame, flow)

    elif method == "splatting_module_summation":
        import splatting

        splatting_module = splatting.Splatting("summation")

        def test_fn():
            splatting_module(frame, flow)

    elif method == "splatting_module_softmax":
        import splatting

        splatting_module = splatting.Splatting("softmax")
        importance_metric = frame.new_ones(
            [frame.shape[0], 1, frame.shape[2], frame.shape[3]]
        )

        def test_fn():
            splatting_module(frame, flow, importance_metric)

    else:
        raise NotImplementedError
    ex_time = (
        timeit.timeit(
            test_fn,
            number=repetitions,
        )
        / repetitions
    )
    print(f"forward \t{batch_size=}\t{spatial_size=}\t{flow_init=}\t{ex_time=}")


def run_test_backward(method, batch_size, spatial_size, flow_init, repetitions=10):
    frame = torch.ones(batch_size, 3, spatial_size, spatial_size)
    if flow_init == "zeros":
        flow = torch.zeros(batch_size, 2, spatial_size, spatial_size)
    elif flow_init == "ones":
        flow = torch.ones(batch_size, 2, spatial_size, spatial_size)
    else:
        raise NotImplementedError
    if method == "splatting_cpp":
        import splatting_cpp

        grad_output = torch.zeros_like(frame)
        grad_frame = torch.zeros_like(frame)
        grad_flow = torch.zeros_like(flow)

        def test_fn():
            splatting_cpp.splatting_backward(
                frame, flow, grad_output, grad_frame, grad_flow
            )

    elif method == "splatting_function":
        import splatting

        frame.requires_grad_(True)
        flow.requires_grad_(True)
        output = splatting.SummationSplattingFunction.apply(frame, flow).sum()

        def test_fn():
            output.backward(retain_graph=True)

    elif method == "splatting_function_summation":
        import splatting

        frame.requires_grad_(True)
        flow.requires_grad_(True)
        output = splatting.splatting_function("summation", frame, flow).sum()

        def test_fn():
            output.backward(retain_graph=True)

    elif method == "splatting_module_summation":
        import splatting

        frame.requires_grad_(True)
        flow.requires_grad_(True)
        splatting_module = splatting.Splatting("summation")
        output = splatting_module(frame, flow).sum()

        def test_fn():
            output.backward(retain_graph=True)

    elif method == "splatting_module_softmax":
        import splatting

        frame.requires_grad_(True)
        flow.requires_grad_(True)
        importance_metric = frame.new_ones(
            [frame.shape[0], 1, frame.shape[2], frame.shape[3]]
        )
        splatting_module = splatting.Splatting("softmax")
        output = splatting_module(frame, flow, importance_metric).sum()

        def test_fn():
            output.backward(retain_graph=True)

    else:
        raise NotImplementedError
    ex_time = (
        timeit.timeit(
            test_fn,
            number=repetitions,
        )
        / repetitions
    )
    print(f"backward\t{batch_size=}\t{spatial_size=}\t{flow_init=}\t{ex_time=}")


def benchmark(method):
    for batch_size in [1, 2, 4]:
        for spatial_size in [2, 8, 16, 256, 1024]:
            for flow_init in ["zeros", "ones"]:
                run_test_forward(method, batch_size, spatial_size, flow_init)
                run_test_backward(method, batch_size, spatial_size, flow_init)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Benchmark splatting implementation")
    parser.add_argument(
        "method",
        type=str,
        choices=[
            "splatting_cpp",
            "splatting_function",
            "splatting_function_summation",
            "splatting_module_summation",
            "splatting_module_softmax",
        ],
        help="What to benchmark",
    )

    args = parser.parse_args()

    benchmark(args.method)
