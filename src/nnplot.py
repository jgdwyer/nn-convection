import numpy as np
import matplotlib
import matplotlib.gridspec as gridspec
import scipy.stats
from sklearn import metrics
import pickle
import os
matplotlib.use('Agg')  # so figs just print to file. Needs to come before mpl
import matplotlib.pyplot as plt
import src.nnload as nnload
import src.nnatmos as nnatmos

unpack = nnload.unpack
pack = nnload.pack
matplotlib.rcParams['agg.path.chunksize'] = 10000

# ---   META PLOTTING SCRIPTS  --- #


def PlotAllFigs(r_str, training_file, validation=True, noshallow=False,
                  rainonly=False):
    # Open the neural network and the preprocessing scheme
    r_mlp_eval, _, errors, x_ppi, y_ppi, x_pp, y_pp, lat, lev, dlev = \
        pickle.load(open('./data/regressors/' + r_str + '.pkl', 'rb'))
    # Load the data from the training/testing/validation file
    x_scl, ypred_scl, ytrue_scl, x_unscl, ypred_unscl, ytrue_unscl = \
        nnload.get_x_y_pred_true(r_str, training_file, minlev=min(lev),
                                 noshallow=False, rainonly=False)
    # Set figure path and create directory if it does not exist
    figpath = './figs/' + r_str + '/'
    # If plotting on training data create a new subfolder
    if validation is False:
        figpath = figpath + 'training_data/'
    if not os.path.exists(figpath):
        os.makedirs(figpath)
    # Do plotting
    print('Beginning to make plots...')
    # Plot model errors over iteration history
    plot_model_error_over_time(errors, r_str, figpath)
    # Plot historgram showing how scaling changed character of input and output
    # data
    check_scaling_distribution(x_unscl, x_scl, ytrue_unscl, ytrue_scl, lat,
                               lev, figpath)
    # Plot histogram showing how well true and predicted values match
    check_output_distribution(ytrue_unscl, ytrue_scl, ypred_unscl, ypred_scl,
                              lat, lev, figpath)
    # Plot means and standard deviations
    plot_means_stds(ytrue_unscl, ypred_unscl, lev, figpath)
    # Plot correlation coefficient, explained variance, and rmse
    plot_error_stats(ytrue_unscl, ypred_unscl, lev, figpath)
    # Plot a "time series" of precipitaiton
    plot_precip(ytrue_unscl, ypred_unscl, dlev, figpath)
    # Plot a scatter plot of true vs predicted precip
    plot_scatter(ytrue_unscl, ypred_unscl, lev, dlev, figpath)
    # Plot the enthalpy conservation
    plot_enthalpy(ytrue_unscl, ypred_unscl, dlev, figpath)
    # Plot some example profiles
    plot_sample_profiles(20, x_unscl, ytrue_unscl, ypred_unscl, lev, figpath)
    # Plot mean, bias, rmse, r^2  (lat vs lev)
    print('Beginning to make contour plots...')
    make_contour_plots(figpath, x_ppi, y_ppi, x_pp, y_pp, r_mlp_eval, lat, lev,
                       training_file)
    print('Done!')


def make_contour_plots(figpath, x_ppi, y_ppi, x_pp, y_pp, r_mlp_eval, lat, lev,
                       datafile):
    # Load data at each level
    Tmean, qmean, Tbias, qbias, rmseT, rmseq, rT, rq = \
          nnload.stats_by_latlev(x_ppi, y_ppi, x_pp, y_pp, r_mlp_eval, lat,
                                 lev, datafile)
    # Make figs
    # True means
    f, ax1, ax2 = plot_contour(Tmean, qmean, lat, lev, avg_hem=False)
    ax1.set_title(r'$\Delta$ Temp True Mean [K/day]')
    ax2.set_title(r'$\Delta$ Humid True Mean [kg/kg/day]')
    f.savefig(figpath + 'latlev_truemean.png', bbox_inches='tight', dpi=450)
    plt.close()
    # Bias from true mean
    f, ax1, ax2 = plot_contour(Tbias, qbias, lat, lev, avg_hem=False)
    ax1.set_title(r'$\Delta$ Temp Mean Bias [K/day]')
    ax2.set_title(r'$\Delta$ Humid Mean Bias [kg/kg/day]')
    f.savefig(figpath + 'latlev_bias.png', bbox_inches='tight', dpi=450)
    plt.close()
    # Root mean squared error
    f, ax1, ax2 = plot_contour(rmseT, rmseq, lat, lev, avg_hem=False)
    ax1.set_title(r'$\Delta$ Temp RMSE [K/day]')
    ax2.set_title(r'$\Delta$ Humid RMSE [kg/kg/day]')
    f.savefig(figpath + 'latlev_rmse.png', bbox_inches='tight', dpi=450)
    plt.close()
    # Pearson r Correlation Coefficient
    f, ax1, ax2 = plot_contour(rT, rq, lat, lev, avg_hem=False)
    ax1.set_title(r'$\Delta$ Temp Correlation Coefficient')
    ax2.set_title(r'$\Delta$ Humid Correlation Coefficient')
    f.savefig(figpath + 'latlev_corrcoeff.png', bbox_inches='tight', dpi=450)
    plt.close()


def plot_contour(T, q, lat, lev, avg_hem=False):
    if avg_hem:
        T, _ = nnload.avg_hem(T, lat, 1)
        q, lat = nnload.avg_hem(q, lat, 1)
    f, (ax1, ax2) = plt.subplots(2, sharex=True)
    cax1 = ax1.contourf(lat, lev, T)
    ax1.set_ylim(1, 0)
    ax1.set_ylabel(r'$\sigma$')
    f.colorbar(cax1, ax=ax1)
    cax2 = ax2.contourf(lat, lev, q)
    ax2.set_ylim(1, 0)
    ax2.set_ylabel(r'$\sigma$')
    f.colorbar(cax2, ax=ax2)
    ax2.set_xlabel('Latitude')
    return f, ax1, ax2


# Plot means and standard deviations
def plot_means_stds(y3_true, y3_pred, lev, figpath):
    fig = plt.figure()
    do_mean_or_std('mean', 'T', y3_true, y3_pred, lev, 1)
    do_mean_or_std('mean', 'q', y3_true, y3_pred, lev, 2)
    do_mean_or_std('std', 'T', y3_true, y3_pred, lev, 3)
    do_mean_or_std('std', 'q', y3_true, y3_pred, lev, 4)
    fig.savefig(figpath + 'regress_means_stds.png', bbox_inches='tight',
                dpi=450)
    plt.close()


# Plot correlation coefficient, explained variance, and rmse
def plot_error_stats(y3_true, y3_pred, lev, figpath):
    fig = plt.figure()
    plt.subplot(2, 2, 1)
    plot_pearsonr(y3_true, y3_pred, 'T', lev, label='T')
    plot_pearsonr(y3_true, y3_pred, 'q', lev, label='q')
    plt.legend(loc="upper left")
    plt.subplot(2, 2, 2)
    plot_expl_var(y3_true, y3_pred, 'T', lev)
    plot_expl_var(y3_true, y3_pred, 'q', lev)
    plt.subplot(2, 2, 3)
    plot_rmse(y3_true, y3_pred, 'T', lev)
    plt.subplot(2, 2, 4)
    plot_rmse(y3_true, y3_pred, 'q', lev)
    fig.savefig(figpath + 'regress_stats.png', bbox_inches='tight', dpi=450)
    plt.close()


# Plot a time series of precipitaiton
def plot_precip(y_true, y_pred, dlev, figpath):
    fig = plt.figure()
    y_true = nnatmos.calc_precip(unpack(y_true, 'q'), dlev)
    y_pred = nnatmos.calc_precip(unpack(y_pred, 'q'), dlev)
    ind = y_true.argsort()
    plt.plot(y_true[ind], label='actual')
    plt.plot(y_pred[ind], alpha=0.6, label='predict')
    plt.legend(loc="upper left")
    plt.title('Precipitation Rate [mm/day]')
    plt.xlabel('Sorted by actual rate')
    fig.savefig(figpath + 'regress_P_rate.png', bbox_inches='tight', dpi=450)
    plt.close()


# Plot a scatter plot of true vs predicted for some variable
def plot_scatter(ytrue_unscl, ypred_unscl, lev, dlev, figpath):
    # Plot scatter of precipitation
    P_true = nnatmos.calc_precip(unpack(ytrue_unscl, 'q'), dlev)
    P_pred = nnatmos.calc_precip(unpack(ypred_unscl, 'q'), dlev)
    f = plt.figure()
    _plot_scatter(plt.gca(), P_true, P_pred,
                  titstr='Precipitation Rate [mm/day]')
    Plessthan0 = sum(P_pred < 0.0)
    Plessthan0pct = 100.*Plessthan0/len(P_pred)
    plt.text(0.01, 0.95, "Pred. P<0 {:.1f}% of time".format(Plessthan0pct),
             transform=plt.gca().transAxes)
    # JGD TO DO: ADD BEST FIT LINE
    f.savefig(figpath + 'P_scatter.png', bbox_inches='tight', dpi=450)
    plt.close()
    # Plot scatters at each level
    # First create new folder
    if not os.path.exists(figpath + '/scatters/'):
        os.makedirs(figpath + '/scatters/')
    for i in range(np.size(lev)):
        f, ax = plt.subplots(1, 2)
        Ttrue = unpack(ytrue_unscl, 'T')[:, i]
        Tpred = unpack(ypred_unscl, 'T')[:, i]
        qtrue = unpack(ytrue_unscl, 'q')[:, i]
        qpred = unpack(ypred_unscl, 'q')[:, i]
        lev_str = r'$\sigma$ = {:.2f}'.format(lev[i])
        _plot_scatter(ax[0], Ttrue, Tpred, titstr='T [K/day] at '+lev_str)
        _plot_scatter(ax[1], qtrue, qpred, titstr='q [g/kg/day] at '+lev_str)
        Teq0 = sum(Ttrue == 0.0) / len(Ttrue) * 100.
        qeq0 = sum(qtrue == 0.0) / len(qtrue) * 100.
        ax[0].text(0.01, 0.95, 'True T=0 {:.1f}% of time'.format(Teq0),
                   transform=ax[0].transAxes)
        ax[1].text(0.01, 0.95, 'True q=0 {:.1f}% of time'.format(qeq0),
                   transform=ax[1].transAxes)
        f.savefig(figpath + '/scatters/Tq_scatter_sigma{:.2f}.png'
                  .format(lev[i]), bbox_inches='tight', dpi=450)
        plt.close()


def _plot_scatter(ax, true, pred, titstr=None):
    ax.scatter(true, pred, s=5, alpha=0.25)
    # Calcualte mins and maxs and set axis bounds appropriately
    xmin = np.min(true)
    xmax = np.max(true)
    ymin = np.min(pred)
    ymax = np.max(pred)
    xymin = np.min([xmin, ymin])
    xymax = np.max([xmax, ymax])
    # Plot 1-1 line
    ax.plot([xymin, xymax], [xymin, xymax], color='k', ls='--')
    ax.set_xlim(xymin, xymax)
    ax.set_ylim(xymin, xymax)
    ax.set_xlabel('True')
    ax.set_ylabel('Predicted')
    if titstr is not None:
        ax.set_title(titstr)


# Plot the enthalpy conservation
def plot_enthalpy(y3_true, y3_pred, dlev, figpath):
    fig = plt.figure()
    plt.subplot(2, 1, 1)
    _plot_enthalpy(y3_true, dlev, label='true')
    plt.legend(loc="upper left")
    plt.subplot(2, 1, 2)
    _plot_enthalpy(y3_pred, dlev, label='predict')
    plt.legend(loc="upper left")
    fig.savefig(figpath + 'regress_enthalpy.png', bbox_inches='tight', dpi=450)
    plt.close()

# ----  PLOTTING SCRIPTS  ---- #


def do_mean_or_std(method, vari, true, pred, lev, ind):
    methods = {'mean': np.mean, 'std': np.std}
    methods_ti = {'mean': 'Mean', 'std': 'Standard Deviation'}
    plt.subplot(2, 2, ind)
    m = lambda x: methods[method](unpack(x, vari), axis=0).T
    plt.plot(m(true), lev, label='true')
    plt.plot(m(pred), lev, label='pred')
    plt.ylim(np.amax(lev), np.amin(lev))
    plt.ylabel('$\sigma$')
    out_str_dict = {'T': 'K/day', 'q': 'g/kg/day'}
    if ind > 2:
        plt.xlabel(out_str_dict[vari])
    plt.title(r'$\Delta$ ' + vari + " " + methods_ti[method])
    plt.legend()


def plot_pearsonr(y_true, y_pred, vari, lev, label=None):
    r = np.empty(y_true.shape[1])
    prob = np.empty(y_true.shape[1])
    for i in range(y_true.shape[1]):
        r[i], prob[i] = scipy.stats.pearsonr(y_true[:, i], y_pred[:, i])
    plt.plot(unpack(r, vari, axis=0), lev, label=label)
    plt.ylim([np.amax(lev), np.amin(lev)])
    plt.ylabel('$\sigma$')
    plt.title('Correlation Coefficient')


def plot_rmse(y_true, y_pred, vari, lev, label=None):
    rmse = np.sqrt(metrics.mean_squared_error(y_true, y_pred,
                                              multioutput='raw_values'))
    rmse = rmse / np.mean(y_true, axis=0)
    plt.plot(unpack(rmse, vari, axis=0), lev, label=label)
    plt.ylim([np.amax(lev), np.amin(lev)])
    plt.ylabel('$\sigma$')
    out_str_dict = {'T': 'K/day', 'q': 'g/kg/day'}
    plt.xlabel(out_str_dict[vari])
    plt.title('Root Mean Squared Error/mean')


def plot_expl_var(y_true, y_pred, vari, lev, label=None):
    expl_var = metrics.explained_variance_score(y_true, y_pred,
                                                multioutput='raw_values')
    plt.plot(unpack(expl_var, vari, axis=0), lev, label=label)
    plt.ylim([np.amax(lev), np.amin(lev)])
    plt.ylabel('$\sigma$')
    plt.title('Explained Variance Regression Score')


def _plot_enthalpy(y, dlev, label=None):
    k = nnatmos.calc_enthalpy(unpack(y, 'T'), unpack(y, 'q'), dlev)
    n, bins, patches = plt.hist(k, 50, alpha=0.5, label=label)
    plt.title('Heating rate needed to conserve column enthalpy')
    plt.xlabel('K/day over column')


def check_scaling_distribution(x_unscl, x_scl, y_unscl, y_scl, lat, lev,
                               figpath):
    # For input variables
    fig, ax = plt.subplots(2, 2)
    _plot_distribution(unpack(x_unscl, 'T'), lat, lev, fig, ax[0, 0],
                       './figs/', 'T (unscaled) [K]', '')
    _plot_distribution(unpack(x_scl, 'T'), lat, lev, fig, ax[0, 1],
                       './figs/', 'T (scaled) []', '')
    _plot_distribution(unpack(x_unscl, 'q'), lat, lev, fig, ax[1, 0],
                       './figs/', 'q (unscaled) [g/kg]', '')
    _plot_distribution(unpack(x_scl, 'q'), lat, lev, fig, ax[1, 1],
                       './figs/', 'q (scaled) []', '')
    fig.savefig(figpath + 'input_scaling_check.png', bbox_inches='tight',
                dpi=450)
    plt.close()
    # For output variables
    fig, ax = plt.subplots(2, 2)
    _plot_distribution(unpack(y_unscl, 'T'), lat, lev, fig, ax[0, 0],
                       './figs/', 'T tend (unscaled) [K/day]', '')
    _plot_distribution(unpack(y_scl, 'T'), lat, lev, fig, ax[0, 1],
                       './figs/', 'T tend (scaled) []', '')
    _plot_distribution(unpack(y_unscl, 'q'), lat, lev, fig, ax[1, 0],
                       './figs/', 'q tend (unscaled) [g/kg/day]', '')
    _plot_distribution(unpack(y_scl, 'q'), lat, lev, fig, ax[1, 1],
                       './figs/', 'q tend(scaled) []', '')
    fig.savefig(figpath + 'output_scaling_check.png', bbox_inches='tight',
                dpi=450)
    plt.close()


def check_output_distribution(yt_unscl, yt_scl, yp_unscl, yp_scl, lat, lev,
                              figpath):
    # For unscaled variables
    fig, ax = plt.subplots(2, 2)
    x1, x2, bins = _plot_distribution(unpack(yt_unscl, 'T'), lat, lev, fig,
                                      ax[0, 0], './figs/',
                                      r'$\Delta$T true [K/day]', '')
    _plot_distribution(unpack(yp_unscl, 'T'), lat, lev, fig,
                       ax[0, 1], './figs/', r'$\Delta$T pred [K/day]', '', x1,
                       x2, bins)
    x1, x2, bins = _plot_distribution(unpack(yt_unscl, 'q'), lat, lev, fig,
                                      ax[1, 0], './figs/',
                                      r'$\Delta$q true [g/kg/day]', '')
    _plot_distribution(unpack(yp_unscl, 'q'), lat, lev, fig, ax[1, 1],
                       './figs/', r'$\Delta$q pred [g/kg/day]', '', x1, x2,
                       bins)
    fig.savefig(figpath + 'output_compare_true_pred_unscaled.png',
                bbox_inches='tight', dpi=450)
    plt.close()
    # For scaled variables
    fig, ax = plt.subplots(2, 2)
    x1, x2, bins = _plot_distribution(unpack(yt_scl, 'T'), lat, lev, fig,
                                      ax[0, 0], './figs/',
                                      r'$\Delta$T true (scld) []', '')
    _plot_distribution(unpack(yp_scl, 'T'), lat, lev, fig, ax[0, 1], './figs/',
                       r'$\Delta$T pred (scld) []', '', x1, x2, bins)
    x1, x2, bins = _plot_distribution(unpack(yt_scl, 'q'), lat, lev, fig,
                                      ax[1, 0], './figs/',
                                      r'$\Delta$q true (scld) []', '')
    _plot_distribution(unpack(yp_scl, 'q'), lat, lev, fig, ax[1, 1], './figs/',
                       r'$\Delta$q pred (scld) []', '', x1, x2, bins)
    fig.savefig(figpath + 'output_compare_true_pred_scaled.png',
                bbox_inches='tight', dpi=450)
    plt.close()


def _plot_distribution(z, lat, lev, fig, ax, figpath, titlestr, xstr, xl=None,
                       xu=None, bins=None):
    """Plots a stack of histograms of log10(data) at all levels"""
    # Initialize the bins and the frequency
    num_bins = 100
    if bins is None:
        bins = np.linspace(np.percentile(z, .02), np.percentile(z, 99.98),
                           num_bins+1)
    n = np.zeros((num_bins, lev.size))
    # Calculate distribution at each level
    for i in range(lev.size):
        n[:, i], _ = np.histogram(z[:, i], bins=bins)
    # Take a logarithm and deal with case where we take log of 0
    n = np.log10(n)
    n_small = np.amin(n[np.isfinite(n)])
    n[np.isinf(n)] = n_small
    # Plot histogram
    ca = ax.contourf(bins[:-1], lev, n.T)
    ax.set_ylim(1, 0)
    if xl is not None:
        ax.set_xlim(xl, xu)
    plt.colorbar(ca, ax=ax)
    ax.set_xlabel(xstr)
    ax.set_ylabel(r'$\sigma$')
    ax.set_title(titlestr)
    xl, xr = ax.set_xlim()
    return xl, xr, bins


def plot_sample_profiles(num_prof, x, ytrue, ypred, lev, figpath, samp=None):
    # Make directory if one does not exist
    if not os.path.exists(figpath + '/samples/'):
        os.makedirs(figpath + '/samples/')
    # Plot some number of sample profiles
    for i in range(num_prof):
        if samp is None:
            samp = np.random.randint(0, x.shape[0])
        sample_filename = figpath + '/samples/' + str(samp) + '.eps'
        plot_sample_profile(x[samp, :], ytrue[samp, :], ypred[samp, :],
                            lev, filename=sample_filename)
        # Need to reset sample number for next iteration
        samp = None


def plot_sample_profile(x, y_true, y_pred, lev, filename=None, pflag=False):
        """Plots the vertical profiles of input T & q and predicted and true
        output tendencies"""
        f, (ax1, ax3) = plt.subplots(1, 2, figsize=(7.5,5))
        T = nnload.unpack(x, 'T', axis=0)
        q = nnload.unpack(x, 'q', axis=0)
        theta = nnatmos.calc_theta(T, lev)
        theta_e = nnatmos.calc_theta_e(T, theta, q)
        theta_e_ns = theta_e[-2]*np.ones(lev.shape)
        # Plot input temperature profile
        if pflag:
            lev = lev*1000
        ax1.plot(theta, lev, label=r'$\theta$')
        ax1.plot(theta_e, lev, label=r'$\theta_e$')
        ax1.plot(theta_e_ns, lev)
        ax1.set_ylim(1000, 250)
        ax1.set_xlim(270, 370)
        ax1.set_title(r'Input Profiles')
        ax1.set_xlabel(r'$\theta$ [K]')
        ax1.grid(True)
        ax1.legend(loc='upper left')
        L = 2.5
        Cp = 1.005
        ax3.plot(Cp * nnload.unpack(y_true, 'T', axis=0), lev, color='red',
                 ls='-', label=r'$\Delta$T true')
        ax3.plot(Cp * nnload.unpack(y_pred, 'T', axis=0), lev, color='red',
                 ls='--', label=r'$\Delta$T pred')
        ax3.plot(L * nnload.unpack(y_true, 'q', axis=0), lev, color='blue',
                 ls='-', label=r'$\Delta$q true')
        ax3.plot(L * nnload.unpack(y_pred, 'q', axis=0), lev, color='blue',
                 ls='--', label=r'$\Delta$q pred')
        ax3.set_ylim(1000, 250)
        ax3.set_xlabel('Cp*T or L*q [kJ/day/kg]')
        ax1.set_ylabel('Pressure [hPa]')
        ax3.set_title('Output Tendencies')
        ax3.legend(loc="upper left")
        ax3.grid(True)
        f.tight_layout()
        # Save file if requested
        if filename is not None:
            f.savefig(filename, bbox_inches='tight')
            plt.close()


def plot_model_error_over_time(errors, mlp_str, fig_dir):
    x = np.arange(errors.shape[0])
    ytix = [.5e-3, 1e-3, 2e-3, 5e-3, 10e-3, 20e-3, 50e-3, 100e-3]
    # Plot error rate vs. iteration number
    fig = plt.figure()
    # Plot training errors from cost function
    plt.semilogy(x, np.squeeze(errors[:, 0]), alpha=0.5, color='blue',
                 label='Training (cost function)')
    plt.semilogy(x, np.squeeze(errors[:, 1]), alpha=0.5, color='blue')
    plt.yticks(ytix, ytix)
    plt.ylim((np.nanmin(errors), np.nanmax(errors)))
    # Plot training errors that are not associated with cost function
    plt.semilogy(x, np.squeeze(errors[:, 4]), alpha=0.5, color='red',
                 label='Training')
    plt.semilogy(x, np.squeeze(errors[:, 5]), alpha=0.5, color='red')
    # Plot cross-validation errors
    plt.semilogy(x, np.squeeze(errors[:, 2]), alpha=0.5, color='green',
                 label='Cross-Val')
    plt.semilogy(x, np.squeeze(errors[:, 3]), alpha=0.5, color='green')
    plt.legend()
    plt.title('Error for ' + mlp_str)
    plt.xlabel('Iteration Number')
    fig.savefig(fig_dir + 'error_history.png', bbox_inches='tight', dpi=450)
    plt.close()


def plot_neural_fortran(training_file, mlp_str, latind=None, timeind=None,
                        ensemble=False):
    # mlp_str = 'X-StandardScaler-qTindi_Y-SimpleY-qTindi_' + \
    #     'Ntrnex100000_r_100R_mom0.9reg1e-06_Niter10000_v3'
    mlp, _, errors, x_ppi, y_ppi, x_pp, y_pp, lat, lev, dlev = \
        pickle.load(open('./data/regressors/' + mlp_str + '.pkl', 'rb'))
    x_unscl, ytrue_unscl, y_dbm_unscl, Ptrue, P_dbm, ten, qen = \
        nnload.load_netcdf_onepoint(training_file, min(lev), latind=latind,
                                    timeind=timeind, ensemble=ensemble)
    ind = 0
    x_scl = nnload.transform_data(x_ppi, x_pp, x_unscl)
    ypred_scl = mlp.predict(x_scl)
    ypred_unscl = nnload.inverse_transform_data(y_ppi, y_pp, ypred_scl)
    Ppred = nnatmos.calc_precip(nnload.unpack(ypred_unscl, 'q'), dlev)
    f, (a1, a2) = plt.subplots(1, 2)
    a1.plot(unpack(ytrue_unscl, 'T')[ind, :], lev, label='GCM dT')
    a1.plot(unpack(ypred_unscl, 'T')[ind, :], lev, label='NN dT')
    a1.plot(unpack(y_dbm_unscl, 'T')[ind, :], lev, label='DBM dT')
    if ensemble:
        for key in ten:
            a1.plot(ten[key], lev, color='gray')
    a1.set_xlabel('K/day')
    a1.set_ylim(1, 0)
    a1.legend()
    a2.plot(unpack(ytrue_unscl, 'q')[ind, :], lev, label='GCM dq')
    a2.plot(unpack(ypred_unscl, 'q')[ind, :], lev, label='NN dq')
    a2.plot(unpack(y_dbm_unscl, 'q')[ind, :], lev, label='DBM dq')
    if ensemble:
        for key in qen:
            a2.plot(qen[key], lev, color='gray')
    a2.set_xlabel('g/kg/day')
    a2.set_ylim(1, 0)
    a2.legend()
    f.savefig('./figs/sampletest/out.png', bbox_inches='tight')
    # Plot inputs
    f, (a1, a2) = plt.subplots(1, 2)
    a1.plot(unpack(x_unscl, 'T')[ind, :].T, lev, label='input T [K]')
    a1.set_ylim(1, 0)
    q0 = unpack(x_unscl, 'q')[ind, :]*1000  # now g/kg
    time_step = 20*60
    dq = unpack(ypred_unscl, 'q')[ind, :]*time_step/3600/24  # now g/kg
    a2.plot(q0, lev, label='input q [kg/kg]')
    a2.plot(q0 + dq, lev, label='q after')
    a2.set_ylim(1, 0)
    plt.xlabel('g/kg')
    plt.legend()
    print('GCM Precip is: {:.2f}'.format(Ptrue[ind]))
    print('MLP Precip is: {:.2f}'.format(Ppred[ind]))
    print('DBM Precip is: {:.2f}'.format(P_dbm[ind]))
    f.savefig('./figs/sampletest/in.png', bbox_inches='tight')


def calc_mse_simple(y_pred, y_true, relflag=False, minlev=None, lev=None):
    """Calculates the mean squared error for scaled outputs and is taken over
       all training examples and levels of T and q
       Args:
        y_pred (float: Nex x N_lev*2): Scaled predicted value of output
        y_true (float Nex x N_lev*2): Scaled true value of output
        relflag (bool): Divide by standard deviation for each var at each lev
                        to somewhat account for difference in strength between
                        convection-only and conv+cond predictions
        minlev (float): Don't consider data above this level when calculating
                        mse
        lev (float: N_lev): Used for calculating minlev
       Returns:
        mse (float, scalar): Mean-Squared error """
    # If requested cut off certain levels
    if minlev is not None:
        if lev is None:
            raise ValueError('Also need to input levels!')
        indlev = np.greater_equal(lev, minlev)
        # For predicted data
        Tp = unpack(y_pred, 'T')[:, indlev]
        qp = unpack(y_pred, 'q')[:, indlev]
        y_pred = pack(Tp, qp)
        # For true data
        Tt = unpack(y_true, 'T')[:, indlev]
        qt = unpack(y_true, 'q')[:, indlev]
        y_true = pack(Tt, qt)
    # Calculate squared difference
    mse = np.square(y_pred - y_true)
    # If looking at relative mean squared error divide by the mean over all
    # examples for each variable and at each level
    if relflag:
        mse = mse/np.abs(np.std(y_true, axis=1))[:, None]
    # Now take mean value over flattened array for all values
    mse = np.mean(mse[np.isfinite(mse)])
    return mse

# ---  CLASSIFICATION METRICS (currently not in use)  --- #


def plot_classifier_hist(pred, y, tistr):
    """Make histograms of the classification scores binned by the
        'strength' of the convection
    Inputs: pred  - predicted classification   (N_samples x 1)
            y     - true T,q tendencies        (N_samples x N_features)
            tistr - used as title and filename (str)"""
    pred = np.squeeze(pred)
    # Calculate convection strength and max it out at 100 for plotting purposes
    conpower = np.sum(np.abs(unpack(y, 'T')), axis=1)
    maxbin = np.floor(.7*np.amax(conpower))
    conpower = np.clip(conpower, 0, maxbin)
    # Calculate some overall statistics
    both1 = np.sum(np.logical_and(pred > 0, conpower > 0))\
        / np.sum(conpower > 0)
    both0 = np.sum(np.logical_and(pred == 0, conpower == 0))\
        / np.sum(conpower == 0)
    pct_cnvct = np.sum(conpower > 0) / len(conpower)
    pct_not_cnvct = np.sum(conpower == 0) / len(conpower)
    # Limit data to times when convection is really happening
    ind = conpower > 0
    pred = pred[ind]
    conpower = conpower[ind]
    # Plot figure
    fig = plt.figure()
    bins = np.linspace(0, maxbin, 100)
    plt.hist(conpower[pred == 0], bins, label='wrong', alpha=0.5)
    plt.hist(conpower[pred == 1], bins, label='right', alpha=0.5)
    plt.legend()
    plt.title(tistr)
    plt.xlabel('"Intensity" of Convection')
    # Write overall statistics including how well we do at classifying when
    # convection does not occur
    postxt = 'Classifier correctly predicts convection: {:.1f}% of time '\
        .format(100.*both1) + '(it convects {:.1f}% of time)'\
        .format(100.*pct_cnvct)
    negtxt = 'Classifier correctly predicts no convection : {:.1f}% of time'\
        .format(100.*both0) + '(it does not convect  %.1f%% of time)'\
        .format(100.*pct_not_cnvct)
    plt.gca().text(.1, .5, postxt, verticalalignment='bottom',
                   horizontalalignment='left', transform=plt.gca().transAxes)
    plt.gca().text(.1, .4, negtxt, verticalalignment='bottom',
                   horizontalalignment='left', transform=plt.gca().transAxes)
    plt.show()
    fig.savefig('./figs/' + 'convection_classifier_' + tistr + '.png',
                bbox_inches='tight', dpi=450)


def plot_roc_curve(mlp_list, mlp_str, X, y_true):
    # For classifier
    auroc_score = []
    fig = plt.figure()
    for ind, mlp in enumerate(mlp_list):
        tp_probs = mlp.predict_proba(X)
        tp_probs = tp_probs[:, 1]
        fpr, tpr, _ = metrics.roc_curve(y_true, tp_probs)
        auroc_score.append(metrics.roc_auc_score(y_true, tp_probs))
        plt.plot(fpr, tpr, label=mlp_str[ind])
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.legend(loc='lower right')
    plt.show()
    fig.savefig('./figs/classify_roc_curves.png', bbox_inches='tight', dpi=450)
    return auroc_score


def plot_classifier_metrics(mlp_list, mlp_str, X, y_true, auroc_score):
    mcc = []
    logloss = []
    tick = np.arange(len(mlp_list))
    for mlp in mlp_list:
        y_pred = mlp.predict(X)
        mcc.append(metrics.matthews_corrcoef(y_true, y_pred))
        logloss.append(metrics.log_loss(y_true, mlp.predict_proba(X)))

    def do_plt(metric, ind, titlestr, mlp_str):
        plt.subplot(1, 3, ind)
        plt.plot(metric, tick, marker='o')
        if ind == 1:
            plt.yticks(tick, mlp_str)
        else:
            plt.setp(plt.gca().get_yticklabels(), visible=False)
        plt.title(titlestr)
        plt.tight_layout()
    fig = plt.figure(102)
    do_plt(mcc, 1, 'Matthews corr. coeff.', mlp_str)
    do_plt(auroc_score, 2, 'Area under ROC curve', mlp_str)
    do_plt(logloss, 3, 'Cross-entropy Loss', mlp_str)
    plt.show()
    fig.savefig('./figs/classify_metrics.png', bbox_inches='tight', dpi=450)
