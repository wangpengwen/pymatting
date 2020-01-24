import scipy.sparse.linalg
import numpy as np
import time
import json
import os
from pymatting import (
    load_image,
    show_images,
    trimap_split,
    make_linear_system,
    LAPLACIANS,
)


def main():
    indices = np.arange(27) + 1
    scale = 0.1
    atol = 1e-5
    image_dir = "data"

    # allow 1% regression
    allowed_error = 0.01

    expected_errors = {
        "cf_laplacian": [
            4.355988465052598,
            7.754267319636701,
            4.747200315117146,
            7.644794385858358,
            4.384527830585845,
            4.531604199822819,
            4.1031381858764835,
            6.0839679119939385,
            4.524651010229449,
            4.358659056252233,
            5.890604883965759,
            3.5985421897613152,
            10.065349782695913,
            2.585264548989054,
            3.7208956259331214,
            16.362808646457598,
            3.8009339105572795,
            6.408594319626463,
            6.017566616442684,
            4.044413987769631,
            11.785953665340037,
            5.430424431633303,
            3.21780354668552,
            5.1231383764470655,
            9.431651112452275,
            13.036791155586041,
            8.988754957709757,
        ],
        "knn_laplacian": [
            3.529027369985819,
            6.779684407351125,
            5.315215932104659,
            7.98386599862108,
            4.201669915857062,
            5.292745196567874,
            4.154624688607045,
            6.386926684070437,
            5.405970320706553,
            4.908653603147019,
            6.359468813893265,
            3.2796344351763556,
            14.078147343580305,
            2.8225579528031197,
            4.833168662156053,
            13.893654956704204,
            4.55905119644519,
            6.511696323731112,
            4.901962902239601,
            4.058804576038566,
            11.250593534800391,
            5.708992860151824,
            3.9937473660706355,
            7.521799056342947,
            12.451095645355371,
            19.559055742483523,
            10.23295095188048,
        ],
        "lbdm_laplacian": [
            4.355917047411817,
            7.755294676926569,
            4.754459256408494,
            7.6527379119497985,
            4.388543223502785,
            4.532265356616695,
            4.101334275889063,
            6.157890368267364,
            4.542514790384632,
            4.354168371741936,
            5.8910132753382936,
            3.597996913221781,
            10.046433903595707,
            2.5842975995911734,
            3.7271507175548657,
            16.377298831555507,
            3.8079423147251483,
            6.411020196265968,
            6.018502476088196,
            4.044885752161074,
            11.78269622620083,
            5.430059151842563,
            3.2183422118639493,
            5.132075679579669,
            9.434882862603411,
            13.025182853722477,
            8.987652819180946,
        ],
        "rw_laplacian": [
            5.41122022101416,
            8.433097819805354,
            5.831135210315725,
            13.5612231500563,
            6.709520989020883,
            7.070404131242503,
            8.386298390789808,
            12.322855420059101,
            8.021969631117862,
            6.081774217141341,
            7.7249956991680255,
            5.764913649046752,
            16.450934622522023,
            5.160830048929572,
            5.1776067921810425,
            19.8520195558823,
            6.6178806558435515,
            8.427877366337041,
            6.402179991723246,
            8.23741566966435,
            13.829571729270182,
            7.287711407153692,
            6.013004768961857,
            8.373112239007229,
            14.367435257885573,
            21.48881471389073,
            15.311157506616729,
        ],
        "uniform_laplacian": [
            9.060169551556976,
            10.412435398963028,
            13.59968223667663,
            13.846523627602492,
            7.920606255132267,
            9.742329228146986,
            9.842485562589646,
            12.678815442427544,
            11.046849004040244,
            9.072405246677807,
            10.491323657975121,
            6.997344821901131,
            16.996103185024563,
            6.70609069103123,
            6.738930012060983,
            13.416425113943234,
            7.636413320373581,
            11.921912128705248,
            8.430136202987251,
            9.091272603814666,
            16.26958162705805,
            10.192918063068861,
            8.775645747372451,
            8.203250649100266,
            12.316984833694821,
            20.0647516222413,
            12.544650300995547,
        ],
    }

    debug = False

    for laplacian in LAPLACIANS:
        laplacian_name = laplacian.__name__
        print("testing", laplacian_name)

        errors = []

        for index, expected_error in zip(indices, expected_errors[laplacian_name]):
            name = f"GT{index:02d}"
            if debug:
                print(name)

            image = load_image(
                f"{image_dir}/input_training_lowres/{name}.png",
                "rgb",
                scale,
                "bilinear",
            )
            trimap = load_image(
                f"{image_dir}/trimap_training_lowres/Trimap1/{name}.png",
                "gray",
                scale,
                "bilinear",
            )
            true_alpha = load_image(
                f"{image_dir}/gt_training_lowres/{name}.png", "gray", scale, "nearest"
            )

            A, b = make_linear_system(laplacian(image), trimap)

            x = scipy.sparse.linalg.spsolve(A, b)

            r = b - A.dot(x)

            norm_r = np.linalg.norm(r)

            alpha = np.clip(x, 0, 1).reshape(trimap.shape)

            is_unknown = trimap_split(trimap, flatten=False)[3]

            difference_unknown = np.abs(alpha - true_alpha)[is_unknown]

            error = np.linalg.norm(difference_unknown)

            additional_error = (error - expected_error) / expected_error

            if additional_error > allowed_error:
                print("Regression:")
                print(laplacian_name)
                print(f"Performance decreased by {100.0 * additional_error:.3f} %")

            assert additional_error < allowed_error

            errors.append(error)

            # visual inspection of alpha results and differences to ground truth
            # show_images([image, trimap, alpha, np.abs(alpha - true_alpha)])

        # print results
        # print(f'"{laplacian_name}": {errors},')


if __name__ == "__main__":
    main()