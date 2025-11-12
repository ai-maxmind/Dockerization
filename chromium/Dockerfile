# syntax=docker/dockerfile:1.7
FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive TZ=UTC LANG=en_US.UTF-8
RUN apt-get update && apt-get install -y --no-install-recommends \
    sudo ca-certificates git curl wget xz-utils build-essential ninja-build ccache python3 python3-pip \
    xvfb xauth x11-xserver-utils fluxbox x11vnc novnc websockify ffmpeg locales \
    && rm -rf /var/lib/apt/lists/*

RUN locale-gen en_US.UTF-8
RUN git clone --depth=1 https://chromium.googlesource.com/chromium/tools/depot_tools.git /opt/depot_tools
ENV PATH=/opt/depot_tools:$PATH

ARG USERNAME=builder
ARG USER_UID=1000
ARG USER_GID=1000
RUN groupadd -g ${USER_GID} ${USERNAME} && useradd -m -u ${USER_UID} -g ${USER_GID} -s /bin/bash ${USERNAME} && \
    echo "${USERNAME} ALL=(ALL) NOPASSWD:ALL" >/etc/sudoers.d/${USERNAME}

USER ${USERNAME}
WORKDIR /work

# Copy scripts
COPY scripts/ /usr/local/bin/
RUN chmod +x /usr/local/bin/*

CMD ["/bin/bash"]
