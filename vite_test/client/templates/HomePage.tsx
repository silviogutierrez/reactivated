import React from "react";
import * as styles from "@client/styles.css";
import {css} from "@linaria/core";

export default () => (
    <div
        className={css`
            background-color: red;
        `}
    >
        <h1 className="bg-indigo-600 text-white text-4xl">Hello Oh My 2!</h1>
        <a className={styles.link} href="/about/">
            About
        </a>
    </div>
);
