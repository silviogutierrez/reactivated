import React from "react";

import * as csstips from "csstips";
import {style} from "typestyle";

const bg = (color: string) => ({backgroundColor: color});

csstips.normalize();
csstips.setupPage("#root");

interface Props {
    children?: React.ReactNode;
}

const HEIGHT = 50;
const WIDTH = 100;

export const Layout = (props: Props) => (
    <div className={style(csstips.fillParent, csstips.vertical)}>
        <div
            className={style(
                csstips.content,
                csstips.height(HEIGHT),
                bg("lightskyblue"),
            )}
        >
            Header
        </div>
        <div className={style(csstips.flex, csstips.horizontal)}>
            <div
                className={style(
                    csstips.content,
                    csstips.width(WIDTH),
                    bg("lightpink"),
                )}
            >
                Sidebar
            </div>
            <div className={style(csstips.flex, bg("darkorange"))}>
                {props.children}
            </div>
            <div
                className={style(
                    csstips.content,
                    csstips.width(WIDTH),
                    bg("limegreen"),
                )}
            >
                Sidebar
            </div>
        </div>
        <div
            className={style(
                csstips.content,
                csstips.height(HEIGHT),
                bg("lightskyblue"),
            )}
        >
            Footer
        </div>
    </div>
);
