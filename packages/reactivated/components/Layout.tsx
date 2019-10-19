import React from "react";

import {style} from "typestyle";
import * as csstips from "csstips";

const bg = (color: string) => ({backgroundColor: color});

csstips.normalize();
csstips.setupPage("#root");

interface Props {
    children?: React.ReactNode;
}

export const Layout = (props: Props) => (
    <div className={style(csstips.fillParent, csstips.vertical)}>
        <div className={style(csstips.content, csstips.height(50), bg("lightskyblue"))}>
            Header
        </div>
        <div className={style(csstips.flex, csstips.horizontal)}>
            <div
                className={style(csstips.content, csstips.width(100), bg("lightpink"))}
            >
                Sidebar
            </div>
            <div className={style(csstips.flex, bg("darkorange"))}>
                {props.children}
            </div>
            <div
                className={style(csstips.content, csstips.width(100), bg("limegreen"))}
            >
                Sidebar
            </div>
        </div>
        <div className={style(csstips.content, csstips.height(50), bg("lightskyblue"))}>
            Footer
        </div>
    </div>
);
